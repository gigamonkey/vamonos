(function () {

  function go() {
    var p = window.location.pathname;
    if (p != '/') {
      name = p.substring(1, p.indexOf('/', 1))
      $('body').append(nameSection(name, []));
    }
    $.ajax('/_/', {
      success: function (x) {
        var db = JSON.parse(x)
        console.log(db);
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
    });
  }

  function nameSection(name, patterns) {
    var div = $('<div>').append($('<h1>').text(name));
    var ul = div.append($('<ul>'));
    $.each(patterns, function (i, p) { pattern(div, ul, name, p); });
    ul.append($('<li>').append(makeForm(name, div)))
    return div;
  }

  function pattern(div, ul, name, p) {
    var del = $('<span>')
      .addClass('delete')
      .text('del')
      .click(function () { deletePattern(name, div, p); });
    ul.append($('<li>').text(p).append(del));
  }

  function makeForm(name, div) {
    return $('<input>').attr('size', 50).change(function (x) {
      submitPattern(name, div, $(x.target).val());
    });
  }

  function submitPattern(name, div, pattern) {
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
        console.log(x);
        div.replaceWith(nameSection(name, JSON.parse(x)));
      },
      error: function (x) {
        alert(x);
      }
    });
  }

  function removeNameButton (name) {
    return $('<span>').addClass('remove')
      .text('remove')
      .click(function () { deleteName(name); });
  }

  function deleteName(name) {
    console.log('remove ' + name);
  }

  $(document).ready(go);

})();
