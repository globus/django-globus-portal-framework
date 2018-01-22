function format(format, obj) {
    if (obj == null) {
        return format;
    }
    if (format == null) {
        return null;
    }
    for (key in obj) {
        console.log("Doing replace on ", format, " with key ", key, " and obj ", obj);
        format = format.replace(RegExp("\\{" + key + "\\}", "gi"), obj[key]);
    }
    return format;
}

function tableForObj(obj, headers) {
    console.log('Creating table for object: ', obj)
    var table = '<table class="table table-striped">';
    var isArray = $.isArray(obj);
    if (!isArray) {
        var a = [obj];
        obj = a;
    }
    table = table + "<tr>";
    if (headers == null) {
        headers = {}
        for (key in obj[0]) {
            headers[key] = key
        }
    }
    for (key in headers) {
        table = table + "<th>";
        var headerVal = headers[key];
        var valType = typeof headerVal;
        if ("object" == valType) {
            headerVal = headerVal['title'];
        }
        table = table + headerVal;
        table = table + "</th>";
    }
    table = table + "</tr>\n";
    var num_rows = obj.length
    for (i = 0; i < num_rows; ++i) {
        var rowobj = obj[i]
        table = table + "<tr>";
        for (key in headers) {
            var headerVal = headers[key];
            var valType = typeof headerVal;
            var formatStr = null;
            if ("object" == valType) {
                formatStr = headerVal['format'];
            }
            var val = null;
            if (formatStr != null) {
                val = format(formatStr, rowobj);
            } else {
                val = rowobj[key];
            }
            table = table + "<td>";
            if ($.isPlainObject(val) || $.isArray(val)) {
                table = table + tableForObj(val);
            } else {
                table = table + val;
            }
            table = table + "</td>";
        }
        table = table + "</tr>";
    }
    table = table + "</table>";
    return table;
}

function createtable(obj, containerid, headers) {
    table = tableForObj(obj, headers);
    $( containerid ).html(table);
}

function createtableJSON(json, containerid, headers) {
    obj = $.parseJSON(json);
    createtable(obj, containerid, headers);
}
