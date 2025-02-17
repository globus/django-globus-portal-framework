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

function _embedBlob(target, blob, {ContentType}) {
  // Most rendering stuff is a thin wrapper for sticking something in an object tag
  const el = document.createElement('object');
  el.type = ContentType;
  el.data = URL.createObjectURL(blob);
  target.appendChild(el);
}

function _preformattedText(target, text) {

}


//////////////////
// Renderers for specific data types
// All renderers have a public call signature of f(targetNode, urlOptions, renderOptions) -> null, and any errors
//  thrown by render function.will be shown to user as a message.
function renderLink(target, {url}, {message}) {
  /**
   * Provide a direct download link for viewing a file later. Useful if we cannot render all or part of a file.
   */
  if (message) {
    const p = document.createElement('p');
    p.innerText = message;
    target.appendChild(p);
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


function _urlToObject(target, urlOptions, renderOptions) {
  // Generic object renderer (image, PDF, short movie clip)
  return _fetchBinaryBlob(urlOptions)
    .then((blob) => _embedBlob(target, blob, urlOptions));
}

function _urlToText(target, urlOptions, renderOptions={is_json: false}) {
  // Displays text in a simple pre tag
  const {is_json} = renderOptions;
  return _fetchText(urlOptions)
    .then((text) => {
      if (is_json) {
        // If "some text mode" fetched only part of the file, the JSON could be incomplete and fail to parse.
        try {
          return JSON.stringify(JSON.parse(text), null, 2);
        } catch (e) {}
      }
      return text;
    })
    .then((text) => {
      const pre = document.createElement('pre');
      pre.innerText = text;
      target.appendChild(pre);
    });
}

RENDERERS.add('application/pdf', _urlToObject)
RENDERERS.add('application/json',
  (t, uo) => _urlToText(t, uo, {is_json: true}),
  (mimetype) => mimetype.toLowerCase().includes('json')
);

// FIXME: Write these: advanced table views to show dependency-light builtin renderers
// RENDERERS.add('text/csv');
// RENDERERS.add('text/tab-separated-values');

RENDERERS.add('text', _urlToText, (mt) => mt.includes('text'));
RENDERERS.add('image', _urlToObject, (mt) => mt.includes('image'));

// Used as part of other renderers, and for standalone error messaging
export {renderLink, _urlToObject, _urlToText};
export {_fetchBinaryBlob, _fetchText, _fetchAuthenticatedContent};

// Exports a plugin registry which other code may choose to extend with custom functions / types
// And lo, a thousand purists cried out and were suddenly silenced
export default RENDERERS;
