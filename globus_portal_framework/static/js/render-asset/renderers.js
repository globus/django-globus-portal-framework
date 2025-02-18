"use strict";
////////////////////////
// Render data in various ways

////////////////////////
// Data retrieval
function _sizeCheck({ContentLength} = fileData, maxSize = (10 * 2 ** 20)) {
  // Throw an error if the file exceeds a size that can be safely handled
  const size = (ContentLength ?? 0);
  if (size > maxSize) {
    throw new Error(`File is too large to preview`);
  }
  return true;
}

function _fetchAuthenticatedContent({url, token} = urlOptions, nBytes = null, rangeStart = 0) {
  const headers = new Headers();
  if (token) {
    headers.set('Authorization', `bearer ${token}`);
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

function _fetchBinaryBlob(urlOptions) {
  // Since binary blobs (like images) must be fetched all at once, there is a hard size limit
  _sizeCheck(urlOptions);
  return _fetchAuthenticatedContent(urlOptions);
}

function _fetchText(urlOptions, maxSize = (10 * 2 ** 20)) {
  // Text files support partial rendering
  const nBytes = (urlOptions.ContentLength > maxSize) ? maxSize : null;
  return _fetchAuthenticatedContent(urlOptions, nBytes)
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

function _addCss(url) {
  const el = document.createElement('link');
  el.rel = 'stylesheet';
  el.href = url;
  el.type = 'text/css';
  document.head.appendChild(el);
}

function _addScript(url) {
  // Synchronously load JS file, only if the renderer needs it
  const el = document.createElement('script');
  el.src = url;
  el.type = 'text/javascript';
  el.defer = false;
  document.head.appendChild(el);
}


function _embedBlob(target, blob, {ContentType}) {
  // Most rendering stuff is a thin wrapper for sticking something in an object tag
  const el = document.createElement('object');
  el.type = ContentType;
  el.data = URL.createObjectURL(blob);
  target.appendChild(el);
  return el;
}


function _sizeToFit(target, content) {
  // Size to fit the parent or the image, whichever is smaller. Good for fixed-resolution things like JPGs.
  // Check if resizing is needed
    const {height: mh, width: mw} = window.visualViewport;
    const {width: rw, height: rh} = content.getBoundingClientRect();

    if (rw <= mw && rh <= mh) {
        // No need to rescale, image is within the bounding box
        return;
    }
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

function _sizeToPage(target, content) {
  // Good for "content renderers" that implement their own zoom, like PDF, PDB, or svg image
  content.style.width = '100%';
  content.style.height = '100vh';
}

//////////////////
// Renderers for specific data types
// All renderers have a public call signature of f(targetNode, urlOptions, renderOptions) -> null, and any errors
//  thrown by render function.will be shown to user as a message.

function renderText(target, urlOptions, {message}) {
  /**
   * Provide a direct download link for viewing a file later. Useful if we cannot render all or part of a file.
   */
  const p = document.createElement('p');
  p.innerText = message;
  target.appendChild(p);
}


function renderLink(target, {url}, {message}) {
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


function _urlToObject(target, urlOptions, {sizer = _sizeToFit} = {}) {
  // Generic object renderer (image, PDF, short movie clip)
  return _fetchBinaryBlob(urlOptions)
    .then((blob) => _embedBlob(target, blob, urlOptions)).then((el) => {
      // Images and PDFs have different resize behavior requirements; allow rescale function to be configurable
      el.onload = () => sizer(target, el);
    });
}

function _urlToText(target, urlOptions, renderOptions) {
  // Displays text in a simple pre tag
  return _fetchText(urlOptions)
    .then((text) => {
      const pre = document.createElement('pre');
      pre.innerText = text;
      target.appendChild(pre);
    });
}


function _urlToCode(target, urlOptions, renderOptions) {
  /**
   * Pretty print text snippets as code
   */
  try {
    // TODO investigate smaller bundles (core, common)
    _addCss("https://unpkg.com/@highlightjs/cdn-assets@11.9.0/styles/default.min.css");
    _addScript("https://unpkg.com/@highlightjs/cdn-assets@11.9.0/highlight.min.js");
  } catch (e) {
    return _urlToText(target, urlOptions);
  }

  return _fetchText(urlOptions)
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

function _urlToTable(target, urlOptions, renderOption) {
  try {
    // _addCss("https://unpkg.com/tabulator-tables@6.3.1/dist/css/tabulator.min.css");
    _addCss("https://unpkg.com/tabulator-tables@6.3.1/dist/css/tabulator_bootstrap4.min.css");
    _addScript("https://unpkg.com/tabulator-tables@6.3.1/dist/js/tabulator.min.js");
  } catch (e) {
    return _urlToText(target, urlOptions);
  }

  return _fetchText(urlOptions).then((text) => {
    const table = new Tabulator(target, {
      data: text.trim(),
      // Note: `text/tab-separated-values` may need custom code in tabulator to process
      importFormat: "csv",
      autoColumns: true,
    });
  });
}


RENDERERS.add('text/csv', _urlToTable);  // tsv ,may
RENDERERS.add('text/javascript', _urlToCode);
RENDERERS.add('application/javascript', _urlToCode);
RENDERERS.add('application/json', _urlToCode);
// Incredibly leaky catchall; see https://mimetype.io/all-types
RENDERERS.add('code', _urlToCode, (mt) => mt.startsWith('text/x-'));

RENDERERS.add('application/pdf', (t, u, r) => _urlToObject(t, u, {sizer: _sizeToPage}));
// Renderers are checked in order, so these are registered last as fallbacks
RENDERERS.add('text', _urlToText, (mt) => mt.includes('text'));
RENDERERS.add('image', _urlToObject, (mt) => mt.includes('image'));


// Used as part of other renderers, and for standalone error messaging
export {renderLink, renderText, _urlToObject, _urlToText};
export {_fetchBinaryBlob, _fetchText, _fetchAuthenticatedContent};

// Exports a plugin registry which other code may choose to extend with custom functions / types
// And lo, a thousand purists cried out and were suddenly silenced
export default RENDERERS;
