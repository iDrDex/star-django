// This code uses simplified React-like approach:
// - there is program state that defines its UI,
// - there is updateUI() function you call to sync actual UI with state,
// - there are event handlers that change state and call updateUI().

var state = {
  tag: '',
  column: '',
  regex: '',
  facet: '',
  tags: [],
};

var derivedState = {};


function updateDerivedState() {
  derivedState.regexValid = state.regex ? checkRegex(state.regex) : null;
  derivedState.tagName = state.tag ? tagNames[state.tag] : null;

  // Calculate facets
  var stats = derivedState.regexValid ? getStats(state.regex) : emptyStats();
  derivedState.facets = stats.facets;
  derivedState.reports = stats.reports;

  // Calculate tag values
  derivedState.values = derivedState.reports.map(function (report, i) {
    return !_.isUndefined(state.tags[i]) ? state.tags[i]
      : report && report.facet ? report.capture || derivedState.tagName : '';
  })
}

function updateUI() {
  updateDerivedState();
  var ds = derivedState;

  // Show that regex is broken
  $('#regex-form-group').toggleClass('has-error', !!(state.regex && !ds.regexValid));

  // Update form
  $('#tag-form [name=tag]').val(state.tag);
  $('#tag-form [name=column]').val(state.column);
  if ($('#tag-form [name=regex]').val() != state.regex)
    $('#tag-form [name=regex]').val(state.regex);
  $('#tag-form button').prop('disabled', !ds.regexValid);

  // Generate facets
  var facetsHTML = ds.facets.map(function (facet) {
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

  // Hide/show column headers
  columns.forEach(function (col) {
    $('th.col-' + col).toggle(!state.column || col == state.column || col == 'sample_id');
  })

  // Generate table
  var visibleColumns = state.column ? ['sample_id', state.column] : columns;
  var rows = samples.map(function (sample, i) {
    var report = ds.reports ? ds.reports[i] : null;
    if (report) {
      if (state.facet && state.facet[0] != '_' && state.facet != report.facet) return '';
      if (state.facet == '__unmatched' && report.facet) return '';
      if (state.facet == '__extra' && report.matches <= 1) return '';
      if (state.facet == '__partial' && !report.partial) return '';
    }

    var mark = ds.regexValid ? getRowMarker(state.regex) : function (s) {return s};
    var cells = visibleColumns.map(function (col) {
      return '<td>' + (col == 'sample_id' ? sample[col] : mark(sample[col])) + '</td>';
    });

    // Tag value input
    cells.unshift(multiline(function(){/*
      <td>
        <div class="input-group">
          <input type="text" class="form-control tag-value-input" data-index="{index}" value="{value}">
        </div>
      </td>
    */}).supplant({value: ds.values[i] || '', index: i}));

    var trClass = _.isUndefined(state.tags[i]) ? '' : 'fixed';
    return '<tr class="' + trClass + '">' + cells.join('') + '</tr>';
  }).join('');
  $('#data-table tbody').html(rows);
}


function checkRegex(regex) {
  try {
    new RegExp(regex)
    return true
  } catch (e) {
    return false;
  }
}

function getRowMarker(regex) {
  var reCapture = new RegExp('(' + state.regex + ')', 'g');
  var i = 0;

  return function (s) {
    return (s + '').replace(reCapture, function (m) {
      return i++ ? '<mark class="bg-danger">' + m + '</mark>'
                 : '<mark>' + m + '</mark>'
    })
  }
}


// Stats and facets calculation
function getStats(regex) {
  var re = new RegExp(regex);
  var reG = new RegExp(regex, 'g');
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
          report.capture = m[1];
          report.facet = m[1] || m[0];
          report.partial = report.partial || isPartialMatch(m, s);
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
  return {facets: [{title: 'All', count: samples.length, facet: ''}], reports: []};
}

function isPartialMatch(m, s) {
  var pre = s.substr(0, m.index);
  var post = s.substr(m.index + m[0].length);

  return m[0].match(/^\w/) && pre.match(/(\w|\w-)$/)
      || m[0].match(/^\d/) && pre.match(/\d\.$/)
      || m[0].match(/\w$/) && post.match(/^(\w|-\w)/)
      || m[0].match(/\d$/) && post.match(/^\.\d/);
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

$('#data-table th.selectable').on('click', function () {
  var col = this.innerText.trim();
  state.column = col != 'sample_id' ? col : '';
  updateUI()
})

$('#data-table').on('keyup change', '.tag-value-input', function () {
  var index = Number($(this).data('index'));
  if (this.value == derivedState.values[index]) return;
  state.tags[index] = this.value;
  // NOTE: we don't call udpateUI() here, but make it this way cause we don't want to loose focus.
  //       There is a way to get both once we switch to Virtual DOM or make a focus explicit state.
  $(this).closest('tr').addClass('fixed');
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

function multiline(fn) {
  if (typeof fn !== 'function') {
    throw new TypeError('Expected a function');
  }

  var reCommentContents = /\/\*!?(?:\@preserve)?[ \t]*(?:\r\n|\n)([\s\S]*?)(?:\r\n|\n)[ \t]*\*\//;
  var match = reCommentContents.exec(fn.toString());

  if (!match) {
    throw new TypeError('Multiline comment missing.');
  }

  return match[1];
};


updateUI(); // Generate first time
