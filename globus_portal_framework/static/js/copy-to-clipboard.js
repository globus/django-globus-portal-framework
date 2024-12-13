/*
Expects a chuck of HTML like this:

  <div class="collapse my-3" id="collapseExample">
    <div class="card card-body">
      <h5 class="text-center">Copy to Clipboard</h5>
        <div id="copy-area" class="alert alert-info" role="alert">
          <div class="row">
            <div class="pt-2 col-md-11 text-center">
              <a id="get-link-url" href="{{https_url}}">{{https_url}}</a>
            </div>
            <div class="col-md-1">
              <button id="copy-button" class="btn btn-primary btn-lg"
                      onclick="copyToClipboard('get-link-url', 'copy-area', '#copy-button');"
                      data-toggle="tooltip" data-placement="top" title="Copied!">
                <i class="fas fa-clipboard"></i>
              </button>
            </div>
          </div>
        </div>
    </div>
  </div>

The widgetId or copy-area is just a place where this function can create a textArea
to select and copy text. It is removed in an instant after the text is copied.
*/

function copyToClipboard(anchorId, widgetId, copyButtonId) {
    var copyText = document.getElementById(anchorId).text;
    var copyWidget = document.getElementById(widgetId);
    var textArea = document.createElement('textarea');

    textArea.value = copyText;
    copyWidget.appendChild(textArea);
    textArea.focus();
    textArea.select();
    document.execCommand('copy');
    copyWidget.removeChild(textArea);

    $(copyButtonId).tooltip('show')
}
