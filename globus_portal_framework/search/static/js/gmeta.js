
// Items that can be bagged by workspace manager.
var bag = {}
var resultItemID = 0;
var resultItems = [];

if (typeof(Storage) !== 'undefined' && 'bag' in sessionStorage) {
    bag = JSON.parse(sessionStorage.bag);
}


var canonicalNames = {
  'Title' :
  ['http://dublincore.org/documents/dcmi-terms#title',
   'http://datacite.org/schema/kernel-3#title',
   'https://docs.globus.org/api/transfer/endpoint#display_name',
   'https://docs.globus.org/api/transfer/endpoint#name',
   'http://globus.org/api/transfer#name',
   'mdf|title'],
  'Collection' :
  ['http://nrdr-ednr.ca/schema/1.0#origin.id',
   'http://globus.org/publish-terms/#collection',
   'mdf|collection',
   'http://globus.org/publish-terms/#publication/collection'],
  'Publication Date' :
  ['http://dublincore.org/documents/dcmi-terms#date',
   'http://dublincore.org/documents/dcmi-terms/#date/available'],
  'Year': ['mdf|year'],
  'Author' :
  ['http://dublincore.org/documents/dcmi-terms#contributor.author',
   'http://datacite.org/schema/kernel-3#contributor/author'],
  'Keywords' :
  ['http://dublincore.org/documents/dcmi-terms#subject',
   'https://docs.globus.org/api/transfer/endpoint#keywords'],
  'Description' :
  ['https://docs.globus.org/api/transfer/endpoint#description',
   'mdf|description'],
  'Owner':
  ['https://docs.globus.org/api/transfer/endpoint#owner_id'],
  'Organization':
  ['https://docs.globus.org/api/transfer/endpoint#organization'],
  'Department':
  ['https://docs.globus.org/api/transfer/endpoint#department'],
  'Visible to Public':
  ['https://docs.globus.org/api/transfer/endpoint#public'],
  'Full Path':
  ['http://globus.org/api/transfer#path'],
  'Last Modified':
  ['http://globus.org/api/transfer#last_modified'],
  'File Size':
  ['http://globus.org/api/transfer#size'],
  'Data Acquisition Method':
  ['http://globus.org/publication-schemas/mdf-base/0.1#data_acquisition_method'],
  'Material Composition':
  ['mdf|composition'],
  'Elements': ['mdf|elements'],
  'Get Data': ['mdf|links']
};

var labelList = ['Collection', 'Publication Date', 'Author',
                 'Description', 'Keywords', 'Owner', 'Organization',
                 'Department',
                 'Visible to Public',
                 'Full Path',
                 'Last Modified',
                 'File Size',
                 'Material Composition',
                 'Data Acquisition Method',
                 'Get Data'
                ];

var labelFormats = {'File Size': 'fileSize',
                    'Publication Date': 'date',
                    'Get Data': 'mdf-links'};

/** Function count the occurrences of substring in a string;
 * @param {String} string   Required. The string;
 * @param {String} subString    Required. The string to search for;
 * @param {Boolean} allowOverlapping    Optional. Default: false;
 * @author Vitim.us http://stackoverflow.com/questions/4009756/how-to-count-string-occurrence-in-string/7924240#7924240
 */
function occurrences(string, subString, allowOverlapping) {

  string += '';
  subString += '';
  if (subString.length <= 0) return (string.length + 1);

  var n = 0,
      pos = 0,
      step = allowOverlapping ? 1 : subString.length;

  while (true) {
    pos = string.indexOf(subString, pos);
    if (pos >= 0) {
      ++n;
      pos += step;
    } else break;
  }
  return n;
}

function truncateString(str, maxLen)
{
  str = String(str);
  if (str.length < maxLen) {
    return str;
  } else {
    var retString = str.substring(0, maxLen - 3) + '...';
    // Watch out for getting truncated in the middle of an <em> tag
    if (occurrences(retString, '<em>', false) >
        occurrences(retString, '</em>', false)) {
      retString = retString + '</em>';
    }
    return retString;
  }

}

// A set of date format strings that we try when humanizing a date value
// These correspond to accepted formats in the datasearch mapping template
var search_time_formats = [
  null, // Null indicates just the default parser from moment.js
  'YYYY-MM-DDTHH:mm:ssZ',
  'YYYY/MM/DD HH:mm:ss Z',
  'YYYY/MM/DD Z',
  'YYYY-MM-DD HH:mm:ss',
  'YYYY-MM-DD',
  'YYYY-MM'
];

function humanizeValue(formatString, value)
{
  if (value == null) {
    return value;
  }
  try {
    if ('from' in value && 'to' in value) {
      var from_val = value['from'];
      var to_val = value['to'];
      return humanizeValue(formatString, from_val) + ' - ' +
        humanizeValue(formatString, to_val);
    }
  } catch(error) {
    // Value was not an object with from and to
  }

  // If input value is an array, we'll return an array of humanized values
  // assuming that the format for each element is the same as the input
  if (value.constructor === Array) {
    var humanArray = [];
    for (i = 0; i < value.length; i++) {
      var childVal = value[i];
      try {
        humanArray.push(humanizeValue(formatString, childVal));
      } catch(err) {
        humanArray.push(childVal);
      }
    }
    return humanArray;
  }
  switch (formatString) {
  case 'fileSize':
    // If it is a value from an open-ended range, we leave it blank
    if (value === '*') {
      value = '';
    } else {
      value = Humanize.fileSize(value);
    }
    break;
  case 'date':
    for (var i = 0; i < search_time_formats.length; i++) {
      var try_format = search_time_formats[i];
      try {
        var dateValue = null;
        if (try_format == null) {
          dateValue = moment(value);
        } else {
          dateValue = moment(value, try_format);
        }
        if (dateValue != null) {
          value = dateValue.format('LLL');
          break;
        }
      } catch (err) {
        // Empty as just try the next format in the list
      }
    }
    break;
  case 'mdf-links':
    // Links is an object with other links under them
    var links = '';
    for (var linkName in value) {
      var linkVal = value[linkName];
      var targetLink = null;
      try {
        if ('globus_endpoint' in linkVal) {
          var path = linkVal['path'];
          var lastSlashLoc = path.lastIndexOf('/');
          // Globus path must be a folder not a file
          if (lastSlashLoc > 0) {
            path = path.substring(0, lastSlashLoc);
          }
          targetLink = 'https://www.globus.org/app/transfer?origin_id=' +
            linkVal['globus_endpoint'] +
            '&origin_path=' +
            encodeURI(path);
        } else if ('http_host' in linkVal) {
          targetLink = linkVal['http_host'] + linkVal['path'];
        }
      } catch (e) {
        // Keys not in the object, so ignore
      }
      if (targetLink != null) {
        links = links + '<a href="'+targetLink+
          '" class="btn btn-primary btn-xs" style="margin-left: 5px;">'+
          linkName + '</a>';
      }
    }
    value = links;
    break;
  }
  return value;
}


function gmetaForEach(gmeta, callback) {
  var data = gmeta['gmeta'];
  data.forEach(function(entry) {
    var subject = entry['subject'];
    var content = entry['content'];
    callback(subject, content);
  });
}

function displayNameForCanonicalName(fullName)
{
  for (var name in canonicalNames) {
    var canonNames = canonicalNames[name];
    for (var i = 0; i < canonNames.length; i++) {
      var canonName = canonNames[i];
      if (canonName == fullName) {
        return name;
      }
    }
  }
  // Not found in table, so try to get the most friendly representation
  var hashLoc = fullName.lastIndexOf('#');
  if (hashLoc > 0) {
    fullName = fullName.substrint(hashLoc + 1);
  }
  return fullName;
}

function valForPathInObject(path, obj)
{
  var pathParts = path.split('|');
  var val = obj;
  for (var i = 0; i < pathParts.length; i++) {
    var pathPart = pathParts[i];
    if (pathPart in val) {
      val = val[pathPart];
    } else {
      val = null;
      break;
    }
  }
  return val;
}

function canonicalVal(name, content)
{
  var allVals = [];
  if (name in canonicalNames) {
    var canonNames = canonicalNames[name];
    for (var i = 0; i < canonNames.length; i++) {
      var canonName = canonNames[i];
      for (var j = 0; j < content.length; j++) {
        var contentEntry = content[j];
        var val = valForPathInObject(canonName, contentEntry);
        if (val !== null) {
          if (name in labelFormats) {
            var humanFormat = labelFormats[name];
            val = humanizeValue(humanFormat, val);
          }
          allVals.push(val);
        }
      }
    }
  }
  return allVals;
}

function canonicalLabel(name, content)
{
  var html = '';
  var vals = canonicalVal(name, content);
  if (vals.length > 0) {
    var hasNonEmpty = false;
    for (var i = 0; i < vals.length; i++) {
      if (vals[i].length > 0) {
        hasNonEmpty = true;
        break;
      }
    }
    if (!hasNonEmpty) {
      return '';
    }
    html = html + name;
    if (vals.length > 1 && !name.endsWith('s')) {
      // make a plural
      html = html + 's';
    }
    html = html + ': ';
    html = html + vals.join('; ');
    html = html + '<br>';
  }
  return html;
}

function htmlForEntry(subject, content, full)
{
  var html = '';
  var titleList = canonicalVal('Title', content);
  var title = null;
  if (titleList.length > 0) {
    title = titleList[0];
  }
  if (title == null) {
    title = subject;
  }
  html = '<div class="result-item">';
  html = html + '<h3 class="search-title"><a href="'+
    '/detail/mdf/' + encodeURIComponent(subject) +
    '" title="' + title + '">'+
    truncateString(title, 120) +
    '</a></h3>\n';
  if (full) {
    html = html + '<div class="result-fields">';
    for (var i = 0; i < labelList.length; i++) {
      html = html + canonicalLabel(labelList[i], content);
    }
//    buttonHTML = bag.hasOwnProperty(subject) ? "In Bag": "Add to Bag";
//    html +=
//    '<div class="result-field">' +
//        '<button ' +
//        'type="button" ' +
//        'onclick="toggleBag(' + resultItemID + ')" ' +
//        'id="result-button-' + resultItemID + '" ' +
//        'class="btn btn-primary btn-sm">' + buttonHTML +
//        '</button>' +
//    '</div>';
//    resultItems[resultItemID] = {
//        'subject': subject,
//        'title': title,
//        'content': content
//    }
//    resultItemID++;
  }
  return html;
}

function toggleBag(resultID) {
    var resultItem = resultItems[resultID]
    if (!bag.hasOwnProperty(resultItem.subject)) {
        var links = parseResultItem(resultItem);
        bag[resultItem.subject] = {
            'title': resultItem.title,
            'links': links
        }
        document.getElementById('result-button-' + resultID).innerHTML = 'In Bag';
    } else {
        delete bag[resultItem.subject];
        document.getElementById('result-button-' + resultID).innerHTML = 'Add to Bag';
    }
    saveBag();
}

function saveBag() {
    console.log(bag);
    if (typeof(Storage) !== 'undefined') {
        sessionStorage.bag = JSON.stringify(bag);
    }
    console.log(bag);
    bagItems = Object.keys(bag).length;
    document.getElementById('bag-btn').innerHTML = '(' + bagItems + ') Bag';
}

function parseResultItem(resultItem) {
    // This is essentially copied code from the 'humanizeValue' function above,
    // with some minor edits to change the protocol to 'globus://'. If this is
    // needed past the SC17 demo, this should be refactored to remove the duplicate
    // code. More likely it should be removed entirely as the metadata will be gotten
    // from dedicated gmeta entry instead of reusing MDFs to hackily fulfil our needs.
    var value = resultItem.content[0].mdf.links;
    var links = [];
    for (var linkName in value) {
      var linkVal = value[linkName];
      var targetLink = null;
      try {
        if ('globus_endpoint' in linkVal) {
          var path = linkVal['path'];
          var lastSlashLoc = path.lastIndexOf('/');
          // Globus path must be a folder not a file
          if (lastSlashLoc > 0) {
            path = path.substring(0, lastSlashLoc);
          }
          targetLink = 'globus://' + linkVal['globus_endpoint'] + ':' + encodeURI(path);
        } else if ('http_host' in linkVal) {
          targetLink = linkVal['http_host'] + linkVal['path'];
        }
      } catch (e) {
        // Keys not in the object, so ignore
      }
      if (targetLink != null) {
        links.push(targetLink);
      }
    }
    return links;
}


// Characters that represent some sort of operation in the query string
// If these are in place, we assume the user is typing a more complex query
// and we shouldn't issue a typeahead query
var querySpecialChars = ' :*[{^/';

function createTextQueryString(searchBoxId)
{
  var searchBox = document.getElementById(searchBoxId);
  var searchString = searchBox.value.trim();
  if (searchString.length < 3) {
    return null;
  }
  for (var i = 0; i < querySpecialChars.length; i++){
    // Get the individual characters as strings
    var testStr = querySpecialChars.substr(i, 1);
    if (searchString.includes(testStr)) {
      // The user has entered a more complex query so return as is
      return searchString;
    }
  }
  // We only have simple characters, so make it a prefix query
  // particularly helpful for typeahead
  searchString = searchString + '*';
  return searchString;
}

function populateSearchResults(gsearchresult, elementId, full, divToShow) {
  var data = gsearchresult['gmeta'];
  if (data == null) {
    return;
  }
  /*
    var dlen = data.length;
    if (dlen == null || typeof(dlen) == 'undefined') {
    return;
    }
  */
  if ('ghighlight' in gsearchresult) {
    replaceGmetaWithHighlight(gsearchresult);
  }

  var divContent = '';
  gmetaForEach(gsearchresult, function(subject, content) {
    divContent = divContent + htmlForEntry(subject, content, full);
  });
  var element = document.getElementById(elementId);
  element.innerHTML= divContent;
  if (divToShow != null) {
    var toShowElement = document.getElementById(divToShow);
    if (toShowElement != null) {
      toShowElement.style.display='inline';
    }
  }
}


function format(format, obj) {
  if (obj == null) {
    return format;
  }
  if (format == null) {
    return null;
  }
  for (var key in obj) {
    console.log('Doing replace on ', format, ' with key ', key, ' and obj ', obj);
    format = format.replace(RegExp('\\{' + key + '\\}', 'gi'), obj[key]);
  }
  return format;
}

