// Known indices, their display name and the query_template to use when
// searching in that index.

var indices = [
  //{index: 'globus_search', name: 'Default', query_template: null},
  {index: 'mdf', name: 'MDF', query_template: 'MDF'},
  {index: 'globus_endpoints', name: 'Endpoints',
   query_template: 'Globus Endpoint'}
];

var api_location = location.origin;

// get the Access Token if set, otherwise null
function getMaybeToken() {
  var metas = document.getElementsByTagName('meta');

  for (var i=0; i < metas.length; i++) {
    if (metas[i].getAttribute('property') == 'access-token') {
      return metas[i].getAttribute('content');
    }
  }

  return null;
}

var searchBoxElementId = 'search-input';

var lastQuery = null;
var lastPage = 0;

function saveElementToSession(elementId, sessionVar) {
  if (elementId != null) {
    var element = document.getElementById(elementId);
    if (element != null) {
      var val = element.value;
      if (val == null) {
        val = element.innerHTML;
      }
      if (val != null) {
        sessionStorage[sessionVar] = val.trim();
      }
      return val;
    }
  }
  return null;
}

function saveSession(queryReturn, pageNum) {
  if (typeof(Storage) !== 'undefined') {
    sessionStorage.lastResult = JSON.stringify(queryReturn);
    sessionStorage.lastPage = pageNum;
    sessionStorage.facetState = JSON.stringify(getFacetState());
    var queryTemplateState = getQueryTemplateState();
    if (queryTemplateState != null) {
      sessionStorage.queryTemplateState = JSON.stringify(queryTemplateState);
    }
    saveElementToSession(searchBoxElementId, 'searchInput');
  }
}

function reloadSession() {
  if (typeof(Storage) !== 'undefined') {
    var searchBoxElement = document.getElementById(searchBoxElementId);
    if ('searchInput' in sessionStorage) {
      searchBoxElement.value = sessionStorage.searchInput;
    }
    if ('lastResult' in sessionStorage) {
      var lastResult = JSON.parse(sessionStorage.lastResult);
      populateSearchResults(lastResult, 'search-result', true, 'results');
      populateFacetResults(lastResult, 'facet-container', false);
      if ('lastPage' in sessionStorage) {
        lastPage = Number(sessionStorage.lastPage);
        populatePagination(lastResult, lastPage);
      }
    }
    if ('facetState' in sessionStorage) {
      setFacetStates(JSON.parse(sessionStorage.facetState));
    }
    if ('queryTemplateState' in sessionStorage) {
      setQueryTemplateState(JSON.parse(sessionStorage.queryTemplateState));
    }

    var url_query = window.location.search;
    if (url_query != null &&
        url_query.startsWith('?q=')) {
      searchBoxElement.value = url_query.substring(3);
      var current_url = window.location.href;
      var new_url = current_url.substring(0,
                                          (current_url.length -url_query.length));
      window.history.replaceState({}, document.title, new_url);
      doSearch(true, null);
    }
  }
}

var resultsPerPage = 10;
var paginationSpan = 10;

function invokeSearch(query, clearFacets, pageNum, indexName) {
  var token = getMaybeToken();
  document.body.style.cursor = 'wait';
  var url = api_location + '/api/v1/search/' + indexName;
  console.log('sending query:', query);
  return $.ajax({
    type: 'POST',
    url: url,
    data: JSON.stringify(query),
    contentType: 'application/json',
    crossDomain: false,
    beforeSend: function (request) {
      if (token != null) {
        request.setRequestHeader('Authorization', 'Bearer ' + token);
      }
      if (!this.crossDomain) {
        csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();
        request.setRequestHeader("X-CSRFToken", csrftoken);
      }
    },
    success: function (gsearchresult) {
      document.body.style.cursor = 'default';
      populateSearchResults(gsearchresult, 'search-result', true, 'results');
      populateFacetResults(gsearchresult,'facet-container', clearFacets);
      lastPage = pageNum;
      populatePagination(gsearchresult, lastPage);
      saveSession(gsearchresult, pageNum);
    },
    error: function(responseData, textStatus, errorCode) {
      document.body.style.cursor = 'default';
    }
  });
}

function doSearch(clearFacets, pageNum) {
  var gSearchRequest = {
    '@datatype': 'GSearchRequest',
    '@version': '2017-09-01'
  };

  var queryString = createTextQueryString(searchBoxElementId);
  if (queryString != null) {
    gSearchRequest['q'] = queryString;
  }

  // var selectedIndexRecord = $('#index-select').getActive();
  var indexSelectElement = document.getElementById('index-select');
  var indexName = indexSelectElement.value;
  var query_templateName = null;
  if ('' == indexName) {
    indexName = 'MDF';
  }

  var selectedIndexRecord = indices.find(function(indexRecord) {
    return indexName == indexRecord.name;
  });


  if (selectedIndexRecord != undefined) {
    if (selectedIndexRecord.query_template != null) {
      gSearchRequest['query_template'] = selectedIndexRecord.query_template;
    }
    // addQueryTemplateToRequest(gSearchRequest, 'query-templates');
    query_templateName = selectedIndexRecord.query_template;
    indexName = selectedIndexRecord.index;
  }

  set_searchreq_advanced_status(gSearchRequest);

  gSearchRequest['limit'] = resultsPerPage;
  if (pageNum != null) {
    gSearchRequest['offset'] = ((pageNum - 1) * resultsPerPage);
  }
  if (! clearFacets) {
    addFilterQueryToRequest(gSearchRequest, query_templateName);
  }

  // Make sure there's something useful in the query
  if (! (('q' in gSearchRequest) || ('query_template' in gSearchRequest) ||
         ('filters' in gSearchRequest))) {
    return;
  }

  // Test if we have functionally the same query and ignore if so
  var sameQuery = (gSearchRequest == lastQuery);
  lastQuery = gSearchRequest;
  lastIndex = indexName;
  if (sameQuery) {
    return;
  }
  return invokeSearch(gSearchRequest, clearFacets, pageNum, indexName);
}

function findQueryTemplateCheckboxByValue(queryTemplateContainerElemId,
                                          value)
{
  var container = document.getElementById(queryTemplateContainerElemId);
  if (container != null) {
    var children = container.childNodes;
    for (var i = 0; i < children.length; i++) {
      var child = children[i];
      if (child.value == value) {
        return child;
      }
    }
  }
  return null;
}

function findCheckedQueryTemplate(queryTemplateContainerElemId) {
  var container = document.getElementById(queryTemplateContainerElemId);
  if (container != null) {
    var children = container.childNodes;
    for (var i = 0; i < children.length; i++) {
      var child = children[i];
      if (child.checked) {
        return child;
      }
    }
  }
  return null;
}

function set_searchreq_advanced_status(gSearchRequest)
{
  var checkbox_elem = document.getElementById('advanced-search-checkbox');
  if (checkbox_elem.checked) {
    gSearchRequest['advanced'] = true;
  }
}

function addQueryTemplateToRequest(gSearchRequest,
                                   queryTemplateContainerElemId)
{
  var childElem = findCheckedQueryTemplate(queryTemplateContainerElemId);
  if (childElem != null && childElem.value != 'all') {
    gSearchRequest['query_template'] = childElem.value;
  }
}

function getQueryTemplateState() {
  var childElem = findCheckedQueryTemplate('query-templates');
  if (childElem != null) {
    return {'query-template': childElem.value};
  } else {
    return null;
  }
}

function setQueryTemplateState(state) {
  var value = state['query-template'];
  if (value != null) {
    var childElem = findQueryTemplateCheckboxByValue('query-templates', value);
    if (childElem != null) {
      childElem.checked = true;
    }
  }
}

function updatePage(newPage) {
  return doSearch(false, newPage);
}

function populatePagination(gsearchresult)
{
  var total = gsearchresult['total'];
  var offset = gsearchresult['offset'];
  var pageNum = (offset / resultsPerPage) + 1;
  var firstPage = pageNum - (paginationSpan / 2);
  if (firstPage < 1) {
    firstPage = 1;
  }
  var lastPage = firstPage + paginationSpan - 1;
  // Use a bitshift op. to force JS to coerce to an int
  var numPages = (((total - 1) / resultsPerPage) >> 0)+ 1;
  if (lastPage > numPages) {
    lastPage = numPages;
    // Now, adjust first page as close to pagination span away as we can
    firstPage = lastPage - paginationSpan + 1;
    if (firstPage < 1) {
      firstPage = 1;
    }
  }
  var paginateHtml = '';

  if (pageNum > 1) {
    paginateHtml = paginateHtml + '<li><a href="#" onClick="updatePage(' + (pageNum - 1) + ');">Prev</a></li>';
  }

  if (firstPage != lastPage) {
    for (var i = firstPage; i <= lastPage; i++) {
      if (i != pageNum) {
        paginateHtml = paginateHtml + '<li><a href="#" onClick="updatePage(' +
          i + ');">' + i + '</a></li>';
      } else {
        paginateHtml = paginateHtml +
          '<li class="active"><a href="#">' + i + '</a></li>';
      }
    }
  }

  if (pageNum < numPages) {
    paginateHtml = paginateHtml + '<li><a href="#" onClick="updatePage(' + (pageNum + 1) + ');">Next</a></li>';
  }

  var paginateDiv = document.getElementById('pagination');
  paginateDiv.innerHTML = paginateHtml;
}



$( document ).ready(function() {

  reloadSession();

  var typeaheadTimeout = null;
  document.getElementById(searchBoxElementId).
    addEventListener('input', function(event) {
      if (typeaheadTimeout) {
        clearTimeout(typeaheadTimeout);
      }
      typeaheadTimeout = setTimeout(function() {
        doSearch(false, null);
      }, 500);
    });


//  bagItems = Object.keys(bag).length;
//  document.getElementById('bag-btn').innerHTML = '(' + bagItems + ') Bag';

  $('#search-form').submit(function(event) {
    // We are explicitly handling all events that would cause submission
    event.preventDefault();
  });
  $('#search-btn').click(function(event) {
    console.log('search btn event: ', event);
    event.preventDefault();
    lastPage = 1; // On full search, return to page 1
    doSearch(false, null);
  });

  $('#search-input').keypress(function(event) {
    if (event.keyCode == 13) {
      // They pressed <enter> so send it
      event.preventDefault();
      lastPage = 1;
      doSearch(false, null);
    }
  });

  $('#bag-btn').click(function(event) {
  // The rest of this code assumes you are not using a library.
  // It can be made less wordy if you use one.
    var url = api_location + '/create_bdbag';

    var form = $(document.createElement( "form" ))
        .attr( {"method": "POST", "action": url} );


    console.log(bag);
    $(document.createElement("input"))
    .attr({ "type": "hidden", "name": "bag", "value": JSON.stringify(bag) })
    .appendTo( form );

    form.appendTo( document.body ).submit();
    bag = {}
    saveBag();
  });

  $('input[type=radio]').click(function() {
    lastPage = 1;
    document.getElementById(searchBoxElementId).value = '';
    doSearch(true, null);
  });

  $('fieldset legend').click(function() {
    if ($(this).parent().children().length == 2)
      $(this).parent().find('div').toggle();
    else {
      $(this).parent().wrapInner('<div>');
      $(this).appendTo($(this).parent().parent());
      $(this).parent().find('div').toggle();
    }
  });
  $('#index-select-dropdown').click(function() {
    $('#index-select').focus();
  });
  $('#index-select').typeahead({
    source: indices,
    autoSelect: true,
    minLength: 0,
    mustSelectItem: true,
    showHintOnFocus: 'all'
  });
  $('#index-select').change(function() {
    doSearch(false, null);
  });
});
