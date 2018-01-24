/*
This file depends on gmeta.js. It needs to be included prior to calling
anything in this file.
*/

var selectedFacets = null;
var checkBoxClass = 'facet-checkbox';
var facetFormats = {'File Size': 'fileSize'};

var facetMaps = {};
var mdfFacetMap = {
  'Tags': {
    'field_name': 'mdf.tags',
    'type': 'match_any'
  },
  'Collection': {
    'field_name': 'mdf.collection',
    'type': 'match_any'
  },
  'Elements': {
    'field_name': 'mdf.elements',
    'type': 'match_any'
  },
  'Composition': {
    'field_name': 'mdf.composition',
    'type': 'match_all'
  },
  'Year': {
    'field_name': 'mdf.year',
    'type': 'range'
  },
  'Resource Type': {
    'field_name': 'mdf.resource_type',
    'type': 'match_any'
  }
};
facetMaps['MDF'] = mdfFacetMap;

var globusEndpointFacetMap = {
  'Owner': {
    'field_name': 'https://docs\\.globus\\.org/api/transfer/endpoint#owner_id',
    'type': 'match_any'
  },
  'Endpoint Keywords': {
    'field_name': 'https://docs\\.globus\\.org/api/transfer/endpoint#keywords',
    'type': 'match_all'
  },
  'Organization': {
    'field_name': 'https://docs\\.globus\\.org/api/transfer/endpoint#organization',
    'type': 'match_any'
  },
  'Public': {
    'field_name': 'https://docs\\.globus\\.org/api/transfer/endpoint#public',
    'type': 'match_any'
  }
};
facetMaps['Globus Endpoint'] = globusEndpointFacetMap;

var bucketValSeparator = '-=-';
var bucketValSeparatorRegex = /-=-/;

function bucketValueCode(facetVal)
{
  if ('value' in facetVal) {
    var value = facetVal['value'];
    if ($.type(value) === 'string') {
      return value;
    } else {
      return value['from'] + bucketValSeparator + value['to'];
    }
  } else {
    return 'Unknown Facet Value';
  }
}

function formatFacetVal(facetVal, facetName)
{
  if (facetName in facetFormats) {
    facetVal = humanizeValue(facetFormats[facetName], facetVal);
  }
  return facetVal;
}


function bucketDisplay(facetVal, facetName)
{
  if (typeof facetVal['value'] === 'object') {
    return formatFacetVal(facetVal['value']['from'], facetName) + ' - ' +
      formatFacetVal(facetVal['value']['to'], facetName);
  } else {
    return formatFacetVal(facetVal['value'], facetName);
  }
}

function bucketHTML(facetName, facetVal)
{
  var checked = '';
  if (selectedFacets != null) {
    if (facetName in selectedFacets) {
      var valueList = selectedFacets[facetName];
      for (var i = 0; i < valueList.length; i++) {
        if (valueList[i] === bucketValueCode(facetVal)) {
          checked = ' checked ';
          break;
        }
      }
    }
  }
  // If a particular facet value isn't checked and has zero count,
  // don't display it
  if (checked == '' && facetVal['count'] == 0) {
    return '';
  }

  var html = '<div class="facet-field"><input type="checkbox" name="' +
      facetName + '" value="' + bucketValueCode(facetVal) +
      '" onChange="doSearch(false)" class="' + checkBoxClass + '"' +
      checked + '/>';
  html = html + truncateString(bucketDisplay(facetVal, facetName), 35);
  html = html + '<span style="float: right">('+ facetVal['count'] +
    ')</span>';
  html = html + '</div>';
  return html;
}


function facetHTML(name, fullName, buckets) {
  var html = '<fieldset class="facet-fieldset">';
  html = html + '<legend>' + name + '</legend>';
  html = html + '<div class="fieldset-container">';
  var emptyFacet = true;
  for (var i = 0; i < buckets.length; i++) {
    var bucketHtml = bucketHTML(fullName, buckets[i]);
    if (bucketHtml != '') {
      html = html + bucketHtml;
      emptyFacet = false;
    }
  }
  if (emptyFacet) {
    return '';
  } else {
    html = html + '</div></fieldset>';
    return html;
  }
}

function getFacetState()
{
  var checkboxes = document.getElementsByClassName(checkBoxClass);
  var filters = {};
  for (var i = 0; i < checkboxes.length; i++) {
    var checkbox = checkboxes[i];
    if (checkbox.checked) {
      console.log('Checkbox: ', checkbox);
      var name = checkbox.name;
      var value = checkbox.value;
      var valList = filters[name];
      if (valList == null) {
        valList = [];
      }
      valList.push(value);
      filters[name] = valList;
    }
  }
  selectedFacets = filters;
  return filters;
}

function inArray(array, val)
{
  var valString = String(val);
  for (var i = 0; i < array.length; i++) {
    if (String(array[i]) === valString) {
      return true;
    }
  }
  return false;
}

function setFacetStates(facetStates)
{
  var checkboxes = document.getElementsByClassName(checkBoxClass);
  for (var i = 0; i < checkboxes.length; i++) {
    var checkbox = checkboxes[i];
    var name = checkbox.name;
    var value = checkbox.value;
    // It will be set to checked if the name is in facetStates
    // and the value is one of the facetStates.
    var checkedState = (name in facetStates &&
                        inArray(facetStates[name], value));
    checkbox.checked = checkedState;
  }
}

function addFilterQueryToRequest(gSearchRequest, templateName)
{
  var filters = getFacetState();
  var reqFilters = [];
  var facetMap = null;
  if (templateName in facetMaps) {
    facetMap = facetMaps[templateName];
  } else {
    console.log('Don\'t know how to filter for template ', templateName);
  }
  for (var filt in filters) {
    var vals = filters[filt];
    if (!(filt in facetMap)) {
      console.log('Don\'t know how to filter on facet ', filt);
      continue;
    }
    var facetMapVals = facetMap[filt];
    if (facetMapVals.type == 'range') {
      var filter_vals = [];
      // Convert range value stored in filter values to value objects as needed
      for (var i = 0; i < vals.length; i++) {
        var range_vals = vals[i].split(bucketValSeparatorRegex, 2);
        if (range_vals.length > 1) {
          filter_vals.push({'from': range_vals[0],
                            'to': range_vals[1]});
        } else {
          filter_vals.push(vals[i]);
        }
      }
      vals = filter_vals;
    }
    var thisFilter = {
      '@datatype': 'GFilter',
      '@version': '2017-09-01',
      // For now, this should get updated to be based on the field
      // being filtered and whether we consider it single/multi-value
      'type': facetMapVals.type,
      'field_name': facetMapVals.field_name,
      'values': vals
    };
    reqFilters.push(thisFilter);
  }
  if (reqFilters.length > 0) {
    gSearchRequest['filters'] = reqFilters;
  }
  return gSearchRequest;
}

function setFacetContent(elementId, content)
{
  var element = document.getElementById(elementId);
  element.innerHTML = content;
}

function populateFacetResults(gsearchresults, elementId, clearSelected)
{
  if (clearSelected) {
    selectedFacets = null;
  }
  var facets = gsearchresults['facet_results'];
  if (facets == null) {
    // make it an empty object to allow fall-through to iteration
    facets = {};
  }
  var content = '';
  for (var facetResultNum in facets) {
    var facetResult = facets[facetResultNum];
    var facetName = facetResult['name'];
    var displayName = displayNameForCanonicalName(facetName);
    var buckets = facetResult['buckets'];
    content = content + facetHTML(displayName,
                                  facetName,
                                  buckets);
  };
  setFacetContent(elementId, content);
  return content;
}
