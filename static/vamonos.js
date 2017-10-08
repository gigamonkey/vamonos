(function () {

  function go() {
    $.ajax('/_/', {
      success: function (x) {
        var db = JSON.parse(x)
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
    var d = $('<div>').append($('<h1>').text(name));
    var ul = d.append($('<ul>'));
    $.each(patterns, function (i, p) { ul.append($('<li>').text(p)); });
    ul.append($('<li>').append(makeForm(name, d)))
    return d;
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
