(function () {

  function go() {
    $.ajax('/_/', {
      success: function (x) {
        $.each(JSON.parse(x), function (k, v) {
          patterns = []
          $.each(v, function (n, p) { patterns.push(p); });
          if (patterns.length > 0) {
            $('body').append(nameSection(k, patterns));
          }
        });
      }
    });
  }

  function nameSection(name, patterns) {
    var d = $('<div>').append($('<h1>').text(name));
    var ul = d.append($('<ul>'));
    $.each(patterns, function (i, p) { ul.append($('<li>').text(p)); });
    return d;
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
