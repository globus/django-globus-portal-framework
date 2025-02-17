import renderers, {renderLink, renderText} from './renderers.js'


function _getURLOptions(url, token) {
  /**
   * Check the file to see if it is a valid target for rendering. For Globus https endpoints, this provides some
   *    valuable information that can make something easier to render
   *  @returns {{url, token, status, statusText, contentType, contentLength, required_scopes}}
   */
  const headers = new Headers({'X-Requested-With': 'XMLHttpRequest'});
  if (token) {
    headers.set('Authorization', `bearer ${token}`);
  }
  return fetch(url, {
    method: 'HEAD',
    headers: headers,
  }).then((response) => {
    const res = {
      // Always provide these fields. Anything more is server-dependent.
      url,
      token,
      'status': response.status,
      'statusText': response.statusText
    };

    if (response.ok) {
      res['ContentType'] = response.headers.get('content-type');
      res['ContentLength'] = response.headers.get('content-length');
    } // else if (response.status === 401) {
    //   // FIXME: NOPE! Head response doesn't have a body. A second request would be needed for globus 401s and better to move that outside to a separate function since this isn't handling 401s anyway
    //   //
    //   // try {
    //   //   // Globus HTTPS endpoints return JSON blobs describing what scopes are needed to see this file
    //   //   // FIXME FIXME FIXME refactor because json is async method, this won't run as written
    //   //   const body = response.json();
    //   //   res['required_scopes'] = body?.authorization_parameters?.required_scopes;
    //   // } catch (e) {
    //   //   // Not every URL will return parser-friendly JSON; err response just won't provide help to fix problem
    //   // }
    // }
    return res;
  });
}


function doRender(target, {url, token, mode = 'auto'}) {
  /**
   * @param {Node | string} target The DOM node to use as rendered content root
   * @param {string} url The full URL of the (usually public) asset to render
   * @param {string} [mode] Optionally specify how to render the file. Usually 'auto' to guess by mimetype, or a
   *  user-specified renderer (like PDB, plot.ly, or leaflet.js)
   */
  target.innerText = "";
  _getURLOptions(url, token).then((urlOptions) => {
    const {ContentType, status, statusText} = urlOptions;
    if (status === 404) {
      return renderText(target, urlOptions, {message: statusText});
    } else if (status !== 200) {
      // Asset cannot be retrieved, but a globus https link may allow auth+access
      // TODO: Add a branch for 401. In the future, we might be able to use required_scopes for incremental reauth.
      throw new Error(statusText);
    }

    let method;
    if (mode && mode !== 'auto') {
      method = renderers.get(mode);
    } else {
      method = renderers.get(ContentType);
    }
    if (!method) {
      return renderLink(target, urlOptions, {message: `Unable to render files of type '${ContentType}'`});
    }
    return method(target, urlOptions);
  }).catch((e) => {
    console.error(e);
    renderLink(target, {url}, {message: e.message});
  });
}


// This is the main script block, and it assumes a specific django template
const render_options = JSON.parse(document.getElementById('render-options').textContent);
const target = document.getElementById('render-target');
doRender(target, render_options);
