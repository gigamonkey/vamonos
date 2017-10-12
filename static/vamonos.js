(function () {

  function go() {
    $.ajax('/_/', { success: addNamesFromDB });
  }

  function addNamesFromDB (db) {
    maybeAddNewName(window.location.pathname, db);
    $.each(_.sortBy(db, ['name']), function (i, item) {
      if (item.patterns.length > 0) {
        $('body').append(nameSection(item));
      }
    });
  }

  function maybeAddNewName(p, db) {
    if (p != '/') {
      name = p.substring(1, p.indexOf('/', 1))
      $('body').append(newNameSection(name, db));
      history.replaceState({}, '', '/');
    }
  }

  function newNameSection(name, db) {

    let div = $('<div>');
    div.append($('<p>')
               .append('No links for ')
               .append($('<b>').text(name))
               .append('. Where would you like it to redirect?'));
    div.append($('<p>').addClass('new-link').append(makeForm(name, div)));
    div.append($('<p>').text('Or did you maybe mean one of these?'));

    let suggestions = $('<p>').addClass('suggestions');

    // FIXME: arguably should do this on the API side.
    let items = _(_.filter(_.sortBy(db, ['name']), function (x) { return x.patterns.length > 0; }));

    let x = items.next();
    while (!x.done) {
      let item = x.value;
      suggestions.append($('<a>').text(item.name).attr('href', '/' + item.name));
      x = items.next();
      if (!x.done) suggestions.append(' | ');
    }

    return div.append(suggestions).addClass('new-name');
  }

  function nameSection(item) {
    let name     = item.name;
    let patterns = _.sortBy(item.patterns, ['args'])

    let div = $('<div>');
    let h1  = $('<h1>').text(name).append(deleteButton(function () { deleteName(name, div); }));
    let ul  = $('<ul>');

    $.each(patterns, function (i, p) { pattern(div, ul, name, p); });
    ul.append($('<li>').append(makeForm(name, div)))

    return div.append(h1).append(ul);
  }

  function pattern(div, ul, name, p) {
    let del = deleteButton(function () { deletePattern(name, div, p.args); })
    ul.append($('<li>').text(p.pattern).append(del));
  }

  function deleteButton(fn) {
    return $('<span>').addClass('delete').text('❌').click(fn)
  }

  function makeForm(name, div) {
    return $('<input>').addClass('url-input').change(function (x) {
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
