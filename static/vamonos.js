(function () {

  function go() {
    maybeAddName(window.location.pathname);
    $.ajax('/_/', { success: addNamesFromDB });
  }

  function maybeAddName(p) {
    if (p != '/') {
      name = p.substring(1, p.indexOf('/', 1))
      $('body').append(nameSection({'name': name, 'patterns': []}).addClass('new-name'));
      history.replaceState({}, '', '/');
    }
  }

  function addNamesFromDB (db) {
    $.each(_.sortBy(db, ['name']), function (i, item) {
      if (item.patterns.length > 0) {
        $('body').append(nameSection(item));
      }
    });
  }

  function nameSection(item) {
    var name     = item.name;
    var patterns = _.sortBy(item.patterns, ['args'])

    var div = $('<div>');
    var h1  = $('<h1>').text(name).append(deleteButton(function () { deleteName(name, div); }));
    var ul  = $('<ul>');

    $.each(patterns, function (i, p) { pattern(div, ul, name, p); });
    ul.append($('<li>').append(makeForm(name, div)))

    return div.append(h1).append(ul);
  }

  function pattern(div, ul, name, p) {
    var del = deleteButton(function () { deletePattern(name, div, p.args); })
    ul.append($('<li>').text(p.pattern).append(del));
  }

  function deleteButton(fn) {
    return $('<span>').addClass('delete').text('❌').click(fn)
  }

  function makeForm(name, div) {
    return $('<input>').attr('size', 50).change(function (x) {
      postPattern(name, div, $(x.target).val());
    });
  }


  // API functions

  function postPattern(name, div, pattern) {
    $.ajax({
      url: '/_/' + name,
      type: 'POST',
      data: { pattern: pattern },
      success: function (x) {
        div.replaceWith(nameSection(x));
      },
      error: function (x) {
        alert(x);
      }
    });
  }

  function deletePattern(name, div, n) {
    $.ajax({
      url: '/_/' + name + '/' + n,
      type: 'DELETE',
      success: function (x) {
        div.replaceWith(nameSection(x));
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
