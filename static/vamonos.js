(function () {

  function go() {
    $.ajax('/_/', { success: addNamesFromDB });
    $.ajax('/!/user', { success: showEmail });
  }

  function showEmail(x) {
    $('body').prepend($('<div>').addClass('login').append($('<span>').text(x.email + ' (domain: ' + x.domain + ')')));
  }

  function addNamesFromDB (db) {
    maybeAddNewName(window.location.pathname, db);
    $.each(_.sortBy(db, ['name']), function (i, item) {
      if (item.patterns.length > 0) {
        $('#container').append(nameSection(item));
      }
    });
  }

  function maybeAddNewName(p, db) {
    if (p != '/') {
      newNameSection(p.substring(1, p.indexOf('/', 1)), db);
      history.replaceState({}, '', '/');
    }
  }

  function newNameSection(name, db) {

    let div = $('<div>');
    div.append($('<p>')
               .append('No links for ')
               .append($('<b>').text(name))
               .append('. Where would you like it to redirect?'));
    var input = makeURLInput(name, div);
    div.append($('<p>').addClass('new-link').append(input));
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
    div.append(suggestions).addClass('new-name');
    $('#container').append(div);
    input.focus();
  }

  function nameSection(item) {
    let name     = item.name;
    let patterns = _.sortBy(item.patterns, ['args'])

    let div = $('<div>');
    let h1  = $('<h1>').text(name).append(' ').append(deleteButton(function () { deleteName(name, div); }));
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
    return $('<i>').addClass('delete').addClass('fa').addClass('fa-minus-circle').attr('aria-hidden', true).click(fn);
  }

  function makeForm(name, div) {
    let i = $('<i>')
        .addClass('add')
        .addClass('fa')
        .addClass('fa-plus-circle')
        .attr('aria-hidden', true)
        .click(function () {
          var input = makeURLInput(name, div);
          i.replaceWith(input);
          input.focus();
        });
    return i;
  }

  function makeURLInput(name, div) {
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
