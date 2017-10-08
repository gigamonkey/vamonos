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
    var patterns = _.map(_.sortBy(item.patterns, ['args']), function (d) { return d.pattern; });

    var div = $('<div>');
    var h1  = $('<h1>').text(name).append(deleteButton(function () { deleteName(name, div); }));
    var ul  = $('<ul>');

    $.each(patterns, function (i, p) { pattern(div, ul, name, p); });
    ul.append($('<li>').append(makeForm(name, div)))

    return div.append(h1).append(ul);
  }

  function pattern(div, ul, name, p) {
    var del = deleteButton(function () { deletePattern(name, div, p); })
    ul.append($('<li>').text(p).append(del));
  }

  function deleteButton(fn) {
    return $('<span>').addClass('delete').text('❌').click(fn)
  }

  function makeForm(name, div) {
    return $('<input>').attr('size', 50).change(function (x) {
      putPattern(name, div, $(x.target).val());
    });
  }


  // API functions

  function putPattern(name, div, pattern) {
    $.ajax({
      url: '/_/' + name + '/' + encodeURIComponent(pattern),
      type: 'PUT',
      success: function (x) {
        console.log(x);
        div.replaceWith(nameSection(x));
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
