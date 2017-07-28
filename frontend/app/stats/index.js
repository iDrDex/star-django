import _ from 'lodash';
import c3 from 'c3';
import * as d3 from 'd3';
import 'c3/c3.css';
import './styles.css';

function showByKeys(table, data, opts={}) {
    const keysData = _.map(data, _.head);
    const keys = _.keys(data[0][1]);

    let dataColumns = {
        total: _.map(data, ([_date, value]) => _.reduce(_.values(value), (a, b) => a + b)),
    };

    _.forEach(keys, (key) => {
        dataColumns[key] = _.map(data, ([_date, value]) => value[key]);
    });

    const chart = c3.generate({
        bindto: `#${table}`,
        data: {
            x: 'x',
            columns: _.concat([
                _.concat('x', keysData),
                opts.showTotal ? _.concat('total', dataColumns.total) : [],
            ], _.map(keys, (key) => _.concat(key, dataColumns[key]))),
        },
        axis: {
            x: {
                type: 'timeseries',
                tick: {
                    format: '%Y-%m-%d',
                },
            },
        },
        legend: {
            show: false,
        },
        tooltip: {
            format: {
                name: opts.mapX || _.identity,
            },
        },
    });

    d3.select(`#${table}_legenda`).insert('div', '.chart').attr('class', 'legend').selectAll('span')
        .data(_.concat(opts.showTotal ? ['total'] : [], keys))
        .enter().append('span')
            .attr('data-id', _.identity)
            .style('background-color', (id) => chart.color(id))
            .html(opts.mapX || _.identity)
            .on('mouseover', (id) => chart.focus(id))
            .on('mouseout', () => chart.revert())
            .on('click', (id) => chart.toggle(id));

    return chart;
}

function showAll(bindto, data) {
    const keys = _.map(data, _.head);
    const values = _.map(data, (i) => i[1]);

    const columns = _.concat(
        [_.concat('x', keys)],
        _.map(
            _.keys(data[0][1]),
            (key) => _.concat(key, _.map(values, (v) => v[key]))));

    const chart = c3.generate({
        bindto,
        data: {
            x: 'x',
            columns,
        },
        axis: {
            x: {
                type: 'timeseries',
                tick: {
                    format: '%Y-%m-%d',
                },
            },
        },
        legend: {
            show: false,
        },
    });

    d3.select(`${bindto}_legenda`).insert('div', '.chart').attr('class', 'legend').selectAll('span')
        .data(_.keys(data[0][1]))
        .enter().append('span')
        .attr('data-id', _.identity)
        .style('background-color', (id) => chart.color(id))
        .html(_.identity)
        .on('mouseover', (id) => chart.focus(id))
        .on('mouseout', () => chart.revert())
        .on('click', (id) => chart.toggle(id));

    return chart;
}

function graphicHtml(table) {
    return `<h3>${_.capitalize(_.lowerCase(table))}</h3><div id="${table}"></div><div id="${table}_legenda"></div>`;
}

function showGeneralStats(data) {
    const general = [
        'platforms', 'platforms_probes', 'series_tag_history',
    ];
    const generalElem = document.getElementById('general_container');

    generalElem.innerHTML = `
    <h3>Tags and Users</h3>
    <div id="users_and_tags"></div>
    <div id="users_and_tags_legenda"></div>
    ${_.join(_.map(general, graphicHtml), '')}
    `;

    const chart = showAll(
        '#users_and_tags',
        _.map(data, ([date, value]) =>
              [date, _.pick(value, ['users', 'tags'])]));

    const charts = _.map(general, (table) =>
        showByKeys(
            table,
            _.map(data, ([date, value]) => [date, value[table]]),
            { showTotal: !_.isEqual(table, 'series_tag_history') })
    );
    return _.concat([chart], charts);
}

function showSamplesStats(data, idToUsername) {
    const samples = [
        'samples', 'sample_annotations', 'sample_validations',
        'sample_tags',
        'concordant_sample_annotations', 'concordant_sample_tags', 'concordant_sample_validations',
        'sample_tags_by_users', 'sample_validations_by_users',
    ];

    const samples_by_users = [
        'sample_tags_by_users', 'sample_validations_by_users',
    ];

    const generalElem = document.getElementById('samples_container');
    generalElem.innerHTML = _.join(_.map(samples, graphicHtml), '');

    return _.map(samples, (table) =>
        showByKeys(
            table,
            _.map(data, ([date, value]) => [date, value[table]]),
            _.includes(samples_by_users, table) ?
                { mapX: idToUsername } : { showTotal: true })
    );
}

function showSeriesStats(data, idToUsername) {
    const series = [
        'series', 'series_annotations', 'series_validations',
        'series_tags',
        'concordant_series_annotations', 'concordant_series_tags', 'concordant_series_validations',
        'series_tags_by_users', 'series_validations_by_users',
    ];

    const series_by_users = [
        'series_tags_by_users', 'series_validations_by_users',
    ];

    const generalElem = document.getElementById('series_container');
    generalElem.innerHTML = _.join(_.map(series, graphicHtml), '');

    return _.map(series, (table) =>
        showByKeys(
            table,
            _.map(data, ([date, value]) => [date, value[table]]),
                _.includes(series_by_users, table) ?
                { mapX: idToUsername } : { showTotal: true })
    );
}

export function showStats(bindto, data, users) {
    function idToUsername(key) {
        return _.get(users, `${key}`, key);
    }

    document.getElementById(bindto).innerHTML = html;

    const generalCharts = showGeneralStats(data);
    const samplesCharts = showSamplesStats(data, idToUsername);
    const seriesCharts = showSeriesStats(data, idToUsername);

    _.forEach([['#general_link', generalCharts],
               ['#samples_link', samplesCharts],
               ['#series_link', seriesCharts],
              ],
              ([id, charts]) =>
              $(id).click(() =>
                          _.map(charts,
                                (chart) => setTimeout(
                                    () => chart.resize(), 0))));
}

const html = `
  <div class="hpanel">
      <div class="hpanel">

      <ul class="nav nav-tabs">
          <li class="active"><a id="general_link" data-toggle="tab" href="#tab-1">General information</a></li>
          <li class=""><a id="samples_link" data-toggle="tab" href="#tab-2">Samples</a></li>
          <li class=""><a id="series_link" data-toggle="tab" href="#tab-3">Series</a></li>
      </ul>
      <div class="tab-content">
          <div id="tab-1" class="tab-pane active">
              <div class="panel-body" id="general_container">
              </div>
          </div>
          <div id="tab-2" class="tab-pane">
              <div class="panel-body" id="samples_container">
              </div>
          </div>
          <div id="tab-3" class="tab-pane">
              <div class="panel-body" id="series_container">
              </div>
          </div>
      </div>
      </div>
  </div>
`;
