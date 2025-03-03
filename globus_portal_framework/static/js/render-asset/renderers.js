"use strict";
////////////////////////
// Render data in various ways
const MAX_SIZE = 2*2**20; // ~2MB



////////////////
// Authorization helpers
function getTokenFromUrl(token_endpoint) {
  /**
   * Return a callable that fetches a token from provided URL. If the token was already retrieved (like on a page
   *  with multiple files), the callable will return the cached Promise.
   *  @returns {function}
   */
  let cache = null;
  return () => {
    const nt = Promise.resolve({access_token: null});

    if (!token_endpoint) {
      // If this is a public asset, return "I have no token to give you" and let render treat it as public
      return nt;
    }

    if (!cache) {
      cache = fetch(token_endpoint)
        .then((resp) => {
          if (resp.ok) {
            return resp.json();
          }
          throw new Error('Token request refused for current user. Make sure you are logged in, and that the application has configured access for this collection');
        }).then(({access_token}) => {
          return {access_token};
        }).catch(() => nt);
    }
    return cache;
  };
}


////////////////////////
// Data retrieval helpers
function checkFileSize({ContentLength} = fileData, maxSize = MAX_SIZE) {
  // Throw an error if the file exceeds a size that can be safely handled. This is because authenticated embeds rely
  //  on loading entire file in memory first, which would be bad for video etc
  const size = (ContentLength ?? 0);
  if (size > maxSize) {
    throw new Error(`File is too large to preview`);
  }
  return true;
}


function fetchAuthenticatedContent(urlOptions, nBytes = null, rangeStart = 0) {
  // Fixme: refactor to general purpose fetcher since auth is optional as written
  const {url, access_token} = urlOptions;

  const headers = new Headers();
  if (access_token) {
    headers.set('Authorization', `bearer ${access_token}`);
  }
  if (nBytes) {
    headers.set('Range', `bytes=${rangeStart}-${rangeStart + nBytes}`);
  }
  return fetch(url, {
    method: 'GET',
    headers: headers,
  }).then((response) => {
    if (response.ok) {
      return response;
    } else {
      console.error(response);
      throw new Error('Error retrieving file contents');
    }
  }).then((resp) => resp.blob());
}


function fetchBinaryBlob(urlOptions) {
  // Since binary blobs (like images) must be fetched all at once, there is a hard size limit
  checkFileSize(urlOptions);
  return fetchAuthenticatedContent(urlOptions);
}


function fetchText(urlOptions, maxSize = (2 * 2 ** 20)) {
  // Text files support partial rendering
  const nBytes = (urlOptions.ContentLength > maxSize) ? maxSize : null;
  return fetchAuthenticatedContent(urlOptions, nBytes)
    .then((blob) => blob.text());
}


///////////////
// Utilities/ abstract methods
class Registry {
  constructor() {
    // Matching items can be identified via exact match, or approximate (according to a bool test function)
    this._name_registry = new Map();
    this._match_registry = new Map();
  }

  add(name, item, test = null) {
    if (this._name_registry.has(name)) {
      console.warn(`User-defined function is overriding existing registry item '${name}'`);
    }
    this._name_registry.set(name, item);
    if (test) {
      this._match_registry.set(name, test);
    }
  }

  get(name) {
    // Find items by either literal match, or an approximate function
    const by_name = this._name_registry.get(name);
    if (by_name) {
      return by_name;
    }
    for (const [key, test_func] of this._match_registry) {
      if (test_func(name)) {
        return this._name_registry.get(key);
      }
    }
    return null;
  }
}

const RENDERERS = new Registry();


function addCss(url) {
  const el = document.createElement('link');
  el.rel = 'stylesheet';
  el.href = url;
  el.type = 'text/css';
  document.head.appendChild(el);
}


function addScript(url) {
  // Synchronously load JS file, only if the renderer needs it
  const el = document.createElement('script');
  el.src = url;
  el.type = 'text/javascript';
  el.defer = false;
  document.head.appendChild(el);
}


function embedBlob(target, blob, {ContentType}) {
  // Many media renderers are a thin wrapper for sticking something in an object tag
  const el = document.createElement('object');
  el.type = ContentType;
  el.data = URL.createObjectURL(blob);
  target.appendChild(el);
  return el;
}


function sizeToFit(target, content) {
  /**
   * Size to fit the parent or the image, whichever is smaller. Good for fixed-resolution things like JPGs.
   */

  const {height: mh, width: mw} = window.visualViewport;
  const {width: rw, height: rh} = content.getBoundingClientRect();

  if (!(rw <= mw && rh <= mh)) {
    // Only rescale if image doesn't fit within bounding box
    const ar = rw / rh;

    let nw = rw;
    let nh = rh;
    if (rw > mw) {
      nw = mw;
      nh = nw / ar;
    }
    if (nh > mh) {
      nh = mh;
      nw = nh * ar;
    }
    content.setAttribute('width', nw);
    content.setAttribute('height', nh);
  }
  // Always center resulting image inside the render area / iframe
  target.style.setProperty("display", "flex");
  target.style.setProperty("justify-content", "center");
  target.style.setProperty("align-items", "center");
  target.style.setProperty("height", "100vh");
}


function sizeToPage(target, content) {
  // Good for "content renderers" that implement their own zoom, like PDF, PDB, or svg image. Fill all available space.
  content.style.width = '100%';
  content.style.height = '100vh';
}


//////////////////
// Renderers for specific data types
// All renderers have a public call signature of f(targetNode, urlOptions, renderOptions) -> null, and any errors
//  thrown by render function.will be shown to user as a message.

function renderText(target, urlOptions, {message}={}) {
  /**
   * Display a message
   */
  const p = document.createElement('p');
  p.innerText = message;
  target.appendChild(p);
}


function renderLink(target, {url}, {message} = {}) {
  /**
   * Provide a direct download link for viewing a file later. Useful if we cannot render all or part of a file.
   */
  if (message) {
    renderText(target, {}, {message})
  }
  const p = document.createElement('p');
  const a = document.createElement('a');

  // Adding a query param causes Globus HTTPS servers to send this as a download
  //  https://docs.globus.org/globus-connect-server/v5/https-access-collections/#request_a_browser_download
  const href = new URL(url);
  href.searchParams.append('download', '1');

  a.href = href.toString();
  a.setAttribute('download', '');
  a.innerText = 'Download the file directly';
  p.appendChild(a);
  target.appendChild(p);
}


function renderUrlToObject(target, urlOptions, {sizer = sizeToFit} = {}) {
  // Generic binary object renderer (image, PDF, short movie clip)
  return fetchBinaryBlob(urlOptions)
    .then((blob) => {
      const el = embedBlob(target, blob, urlOptions);
      // Render a fallback message if object fails to display due to bad video codecs, PDF inside iframe sandbox, etc
      const fb = document.createElement('div');
      renderLink(fb, urlOptions, {message: 'The item failed to render'});
      el.appendChild(fb);
      return el;
    })
    .then((el) => {
      // Once binary item loads, resize according to best behavior (customized to needs of eg image vs pdf)
      el.onload = () => sizer(target, el);
    });
}


function renderUrlToText(target, urlOptions, renderOptions={}) {
  // Displays text in a simple pre tag
  return fetchText(urlOptions)
    .then((text) => {
      const pre = document.createElement('pre');
      pre.innerText = text;
      target.appendChild(pre);
    });
}


function renderUrlToCode(target, urlOptions, renderOptions={}) {
  /**
   * Pretty print text snippets as code
   */
  try {
    // TODO investigate smaller bundles (core, common)
    addCss("https://unpkg.com/@highlightjs/cdn-assets@11.9.0/styles/default.min.css");
    addScript("https://unpkg.com/@highlightjs/cdn-assets@11.9.0/highlight.min.js");
  } catch (e) {
    return renderUrlToText(target, urlOptions);
  }

  return fetchText(urlOptions)
    .then((text) => {
      const pre = document.createElement('pre')
      const c =  document.createElement('code');
      pre.appendChild(c);

      const res = hljs.highlightAuto(text);
      if (res.language) {
        console.debug('HL.JS auto detected language:', res.language);
        c.innerHTML = res.value;
      } else {
        // If hljs did not process the string, treat it as unsafe markup
        console.debug('HL.JS failed to detect language; rendering as text');
        c.innerText = res.value;
      }
      target.appendChild(pre);
    });
}


function renderUrlToTable(target, urlOptions, renderOptions={}) {
  try {
    // _addCss("https://unpkg.com/tabulator-tables@6.3.1/dist/css/tabulator.min.css");
    addCss("https://unpkg.com/tabulator-tables@6.3.1/dist/css/tabulator_bootstrap4.min.css");
    addScript("https://unpkg.com/tabulator-tables@6.3.1/dist/js/tabulator.min.js");
  } catch (e) {
    return renderUrlToText(target, urlOptions);
  }

  return fetchText(urlOptions).then((text) => {
    const table = new Tabulator(target, {
      data: text.trim(),
      // Note: `text/tab-separated-values` may need custom code in tabulator to process
      importFormat: "csv",
      autoColumns: true,
    });
  });
}


///////////////////
// Perform the act of rendering on a page in a re-usable way
function _getURLOptions(url, access_token) {
  /**
   * Check the file to see if it is a valid target for rendering. For Globus https endpoints, this provides some
   *    valuable information that can make something easier to render
   *  @returns {{url, access_token, status, statusText, contentType, contentLength, required_scopes}}
   */
  const headers = new Headers({'X-Requested-With': 'XMLHttpRequest'});
  if (access_token) {
    headers.set('Authorization', `bearer ${access_token}`);
  }
  return fetch(url, {
    method: 'HEAD',
    headers: headers,
  }).then((response) => {
    const res = {
      // Always provide these fields. Anything more is server-dependent.
      url,
      access_token,
      'status': response.status,
      'statusText': response.statusText
    };

    if (response.ok) {
      res['ContentType'] = response.headers.get('content-type');
      res['ContentLength'] = response.headers.get('content-length');
    }
    // TODO FUTURE: This function does not try to handle 401 cases, such as determining `required_scopes` from globus GET response
    return res;
  });
}


function doRender(target, pageOptions, getToken) {
  /**
   * Make an (authenticated) request to retrieve the file
   *
   * @param {Node | string} target The DOM node to use as rendered content root
   * @param {object} pageOptions An object containing options used to render this asset. Must answer the questions
   *  "where is the asset" and "tell me how to access it".
   * @param pageOptions.url
   * @param [pageOptions.access_token] Avoid embedding this in the DOM whenever possible
   * @param [pageOptions.token_endpoint] A django-provided URL for where to get read-only file view credentials
   * @param {string} url The full URL of the (usually public) asset to render
   * @param {string} [mode] Optionally specify how to render the file. Usually 'auto' to guess by mimetype, or a
   *  user-specified renderer (like PDB, plot.ly, or leaflet.js)
   */
  const {url, token_endpoint, render_mode = 'auto'} = pageOptions;

  target.innerText = "";

  // On a page with multiple files, this can be passed explicitly to use a shared cache and only fetch the token once
  getToken = getToken || getTokenFromUrl(token_endpoint);

  // Perform all actions required to render an asset on the page, incl (authorized) data retrieval
  return getToken().then(({access_token}) => {
      _getURLOptions(url, access_token).then((urlOptions) => {
        const {ContentType, status, statusText} = urlOptions;
        if (status === 404) {
          return renderText(target, urlOptions, {message: statusText});
        } else if (status !== 200) {
          // Asset cannot be retrieved, but a globus https link may allow auth+access
          // TODO: Add a branch for 401. In the future, we might be able to use required_scopes for incremental reauth.
          throw new Error(statusText);
        }

        let method;
        if (render_mode && render_mode !== 'auto') {
          method = RENDERERS.get(render_mode);
        } else {
          method = RENDERERS.get(ContentType);
        }
        if (!method) {
          return renderLink(target, urlOptions, {message: `Unable to render files of type '${ContentType}'`});
        }
        return method(target, urlOptions);
      }).catch((e) => {
        console.error(e);
        renderLink(target, {url}, {message: e.message});
      });
  });
}


/////////////
// Populate the registry with default render helpers
RENDERERS.add(null, renderLink);  // Very rare file extensions may return no content-type at all.
// Known issue: PDFs don't render inside a sandboxed iframe. If your dataset is PDF heavy, customize template to remove the sandbox
RENDERERS.add('application/pdf', (t, u, r) => renderUrlToObject(t, u, {sizer: sizeToPage}));
RENDERERS.add('text/csv', renderUrlToTable); // We may need extra code to handle TSVs w/current library
RENDERERS.add('text/javascript', renderUrlToCode);
RENDERERS.add('application/javascript', renderUrlToCode);
RENDERERS.add('application/json', renderUrlToCode);
// Incredibly leaky catchall; see https://mimetype.io/all-types
RENDERERS.add('code', renderUrlToCode, (mt) => mt.startsWith('text/x-'));

// Renderers are checked in order, so these are registered last as fallbacks
RENDERERS.add('text', renderUrlToText, (mt) => mt.includes('text'));
RENDERERS.add('image', renderUrlToObject, (mt) => mt.includes('image'));

////////
// All renderers have the standard call signature f(t, {u}, {r}) -> Promise
// Useful generic renderers
export {renderLink, renderText};
// Specific renderers with limited customization via renderOptions arg
export {renderUrlToObject, renderUrlToText, renderUrlToCode, renderUrlToTable};

// Helpers used to build your own renderer
export {
  fetchBinaryBlob, fetchText, fetchAuthenticatedContent,
  addCss, addScript,
  sizeToPage, sizeToFit,
  embedBlob,
};


export { doRender };
// Exports a plugin registry which other code may choose to extend with custom functions / types
// And lo, a thousand purists cried out and were suddenly silenced
export default RENDERERS;
