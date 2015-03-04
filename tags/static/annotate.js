var state = {};

function updateUI() {
  state.regex = state.regex || '';
  state.facet = state.facet || '';

  // Show that regex is broken
  var re = null;
  if (state.regex) {
    try {
      re = new RegExp(state.regex)
    } catch (e) {}
  }
  $('#regex-form-group').toggleClass('has-error', !!(state.regex && !re));

  // Select current column
  $('#tag-form [name=column]').val(state.column);

  // Hide/show column headers
  columns.forEach(function (col) {
    $('th.col-' + col).toggle(!state.column || col == state.column || col == 'sample_id');
  })

  // Mark matched function
  var reCapture = re ? new RegExp('(' + state.regex + ')', 'g') : null;
  function getMark() {
    if (!re) return function (s) {return s};

    var i = 0;

    return function (s) {
      return (s + '').replace(reCapture, function (m) {
        return i++ ? '<mark class="bg-danger">' + m + '</mark>'
                   : '<mark>' + m + '</mark>'
      })
    }
  }

  // Generate facets
  var stats = re ? getStats(state.regex) : emptyStats();
  var facetsHTML = stats.facets.map(function (facet) {
    return '<li role="presentation" class="{active}"><a href="#" data-facet="{facet}" class="text-{cls}">{icon}<b>{title}</b> ({count})</a></li>'
      .supplant({
        facet: facet.facet,
        title: facet.title || facet.facet,
        count: facet.count,
        cls: facet.cls || '',
        icon: facet.cls == 'danger' ? '<span class="glyphicon glyphicon-exclamation-sign"></span> ' : '',
        active: facet.facet == (state.facet) ? 'active' : ''})
  }).join('');
  $('#facets').html(facetsHTML);

  // Generate table
  var visibleColumns = state.column ? ['sample_id', state.column] : columns;
  var rows = samples.map(function (sample, i) {
    var report = stats.reports ? stats.reports[i] : null;
    if (report) {
      if (state.facet && state.facet[0] != '_' && state.facet != report.facet) return '';
      if (state.facet == '__unmatched' && report.facet) return '';
      if (state.facet == '__extra' && report.matches <= 1) return '';
      if (state.facet == '__partial' && !report.partial) return '';
    }

    var mark = getMark();
    var cells = visibleColumns.map(function (col) {
      return '<td>' + (col == 'sample_id' ? sample[col] : mark(sample[col])) + '</td>';
    });
    return '<tr>' + cells.join('') + '</tr>';
  }).join('');
  $('#data-table tbody').html(rows);
}


function getStats(regex) {
  var re = new RegExp(regex);
  var reG = new RegExp(regex, 'g');

  function isPartial(m, s) {
    var pre = s.substr(0, m.index);
    var post = s.substr(m.index + m[0].length);

    return m[0].match(/^\w/) && pre.match(/(\w|\w-)$/)
        || m[0].match(/^\d/) && pre.match(/\d\.$/)
        || m[0].match(/\w$/) && post.match(/^(\w|-\w)/)
        || m[0].match(/\d$/) && post.match(/^\.\d/);
  }

  var reports = [];
  var cols = state.column? [state.column] : _.without(columns, 'sample_id');

  // Count matches
  samples.forEach(function (sample) {
    var m = null, i, s;

    var report = {matches: 0, facet: ''};
    reports.push(report);

    for (i = 0; i < cols.length; i++) {
      s = sample[cols[i]] + '';
      if (!m) {
        m = re.exec(s);
        if (m) {
          report.facet = m[1] || m[0];
          report.partial = report.partial || isPartial(m, s);
        }
      }
      report.matches += (s.match(reG) || '').length;
    }
  });

  // Prepare structure
  var counts = _.countBy(reports, 'facet');
  var facets = _.chain(counts).keys().compact().map(function (facet) {
    return {facet: facet, count: counts[facet]};
  }).value();

  facets.unshift({title: 'All', count: samples.length, facet: ''});
  if (counts[''])
    facets.push({title: 'Unmatched', count: counts[''], facet: '__unmatched', cls: 'danger'});

  var xMatches = reports.filter(function (r) {return r.matches > 1}).length;
  if (xMatches)
    facets.push({title: 'Extra Matches', count: xMatches, facet: '__extra', cls: 'danger'});

  var pMatches = reports.filter(function (r) {return r.partial}).length;
  if (pMatches)
    facets.push({title: 'Partial Matches', count: pMatches, facet: '__partial', cls: 'danger'});

  return {facets: facets, reports: reports};
}

function emptyStats() {
  return {facets: [{title: 'All', count: samples.length, facet: ''}]};
}


// Event listeners
$('#tag-form [name=regex]').on('keyup paste', function () {
  var element = this;
  setTimeout(function () {
    state.regex = element.value;
    updateUI()
  }, 50);
})

$('#tag-form [name=column]').on('change', function () {
  state.column = this.value;
  updateUI()
})

$('#facets').on('click', 'a', function () {
  state.facet = $(this).data('facet');
  updateUI()
})

$('#data-table th').on('click', function () {
  var col = this.innerText.trim();
  state.column = col != 'sample_id' ? col : '';
  updateUI()
})


// extend js
if (!String.prototype.supplant) {
    String.prototype.supplant = function (o) {
        return this.replace(
            /\{([^{}]*)\}/g,
            function (a, b) {
                var r = o[b];
                return typeof r === 'string' || typeof r === 'number' ? r : a;
            }
        );
    };
}
