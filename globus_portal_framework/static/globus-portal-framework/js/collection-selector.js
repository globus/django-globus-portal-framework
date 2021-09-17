

class CollectionSelector {
  operationLsUrl = '/api/transfer/operation-ls';
  name = 'collectionSelector';
  collection;
  path;
  data;
  lastSelected;

  constructor(collection, path, operationLsUrl) {
    this.collection = collection;
    this.path = path || '/';
    this.operationLsUrl = operationLsUrl || this.operationLsUrl
    this.data = [];

    var cls = this
    $( "#collectionSelectorUp" ).on( "click", function() {
      var p = cls.up(cls.path)
      cls.chdir(p)
    });
    $( "#collectionSelectorRefresh" ).on( "click", function() { cls.chdir(cls.path) });
    $( "#collectionSelectorPath" ).on( "change", function() { cls.chdir($(this).val())});
    $( "#collectionSelectorFiles" ).selectable({
      stop: function() {
        $( ".ui-selected", this ).each(function() {

        });
      }
    });
    $( "#collectionSelectorFiles" ).dblclick( function() {
      $( ".ui-selected", this ).each(function() {
        var file = cls.getFile($(this).text())
        if (file.type == 'dir') {
          var new_path = cls.joinUnix([cls.path, file.name])
          cls.chdir(new_path);
        }
      })
    })
    $( "#collectionSelectorWebapp" ).on( "click", function() {
      let base_url = 'https://app.globus.org/file-manager';
      var path = encodeURIComponent(cls.path);
      var url = base_url + '?origin_id=' + cls.collection + '&origin_path=' + path;
      window.open(url, '_blank');
    });
    this.chdir(this.path);
  }
}


CollectionSelector.prototype.chdir = function(new_path) {
  cls = this
  this.path = new_path
  $( "#collectionSelectorCollection" ).val(this.collection);
  $( "#collectionSelectorPath" ).val(this.path);
  $( "#collectionSelectorError").hide()

  $( "#collectionSelectorFiles" ).empty().append($( "<td/>" ).append("Loading..."))

  $.getJSON({
    url: this.operationLsUrl,
    data: { collection: this.collection, path: this.path },
    success: function(data) {
      $( "#collectionSelectorFiles" ).empty()
      cls.data = data;
      $.each(cls.data.DATA, function(key, val) {
        var td = $( "<td/>" )
        if (val.type == 'dir') {
          td.append('<i class="fas fa-folder-open"></i>')
        } else {
          td.append('<i class="fas fa-file"></i>')
        }
        td.append(val.name)
        tr = $( "<tr/>", {
          "class": "ui-widget-content",
        }).append(td).appendTo( "#collectionSelectorFiles" )
      });
    },
    error: function(response) {
      $( "#collectionSelectorError" ).show()
      $( "#collectionSelectorError" ).text(response.responseJSON.message)

      console.error(response.responseJSON)
    }
  })
}

CollectionSelector.prototype.up = function(path) {
  var p = path.split('/').slice(0, -1).join('/');
  return p || '/'
}

CollectionSelector.prototype.getFile = function(filename) {
  var return_value = null;

  $.each(this.data.DATA, function(index, file) {
    if (filename == file.name) {
      return_value = file
    }
  })
  return return_value;
}

CollectionSelector.prototype.joinUnix = function(paths) {
  return paths.join('/').replace('//', '/')
}
