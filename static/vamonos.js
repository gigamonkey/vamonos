(function () {

  function go() {
    maybeAddName(window.location.pathname);
    $.ajax('/_/', { success: addNamesFromDB });
  }

  function maybeAddName(p) {
    if (p != '/') {
      name = p.substring(1, p.indexOf('/', 1))
      $('body').append(nameSection(name, []));
    }
  }

  function addNamesFromDB (data) {
        var db = JSON.parse(data)
        var keys = _.keys(db)
        keys.sort()
        $.each(keys, function (i, k) {
          var patterns = _.map(db[k], function (p, n) { return { args: parseInt(n), pattern: p }; });
          if (patterns.length > 0) {
            sorted = _.map(_.sortBy(patterns, ['args']), function (d) { return d.pattern; });
            $('body').append(nameSection(k, sorted));
          }
        });
      }

  function nameSection(name, patterns) {
    var div = $('<div>');
    div.append($('<h1>').text(name).append(deleteButton(function () { deleteName(name, div); })));
    var ul = div.append($('<ul>'));
    $.each(patterns, function (i, p) { pattern(div, ul, name, p); });
    ul.append($('<li>').append(makeForm(name, div)))
    return div;
  }

  function pattern(div, ul, name, p) {
    var del = deleteButton(function () { deletePattern(name, div, p); })
    ul.append($('<li>').text(p).append(del));
  }

  function deleteButton(fn) {
    return $('<span>').addClass('delete').text('del').click(fn)
  }

  function makeForm(name, div) {
    return $('<input>').attr('size', 50).change(function (x) {
      putPattern(name, div, $(x.target).val());
    });
  }

  function putPattern(name, div, pattern) {
    $.ajax({
      url: '/_/' + name + '/' + encodeURIComponent(pattern),
      type: 'PUT',
      success: function (x) {
        div.replaceWith(nameSection(name, JSON.parse(x)));
      },
      error: function (x) {
        alert(x);
      }
    });
  }

  function deletePattern(name, div, pattern) {
    $.ajax({
      url: '/_/' + name + '/' + encodeURIComponent(pattern),
      type: 'DELETE',
      success: function (x) {
        div.replaceWith(nameSection(name, JSON.parse(x)));
      },
      error: function (x) {
        alert(x);
      }
    });
  }

  function deleteName(name, div) {
    $.ajax({
      url: '/_/' + name,
      type: 'DELETE',
      success: function (x) { div.remove() },
      error: function (x) { alert(x); }
    });
  }

  $(document).ready(go);

})();
