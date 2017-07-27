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
        bindto: `#${table}_by_species`,
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
            show: !opts.mapX,
        },
    });
    if (opts.mapX) {
        d3.select(`#${table}_legenda`).insert('div', '.chart').attr('class', 'legend').selectAll('span')
            .data(keys)
            .enter().append('span')
                .attr('data-id', _.identity)
                .style('background-color', (id) => chart.color(id))
                .html(opts.mapX)
                .on('mouseover', (id) => chart.focus(id))
                .on('mouseout', () => chart.revert())
                .on('click', (id) => chart.toggle(id));

    }
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
    });
}

export function showStats(bindto, data, users) {

    const bySpecies = [
        'platforms_probes', 'platforms',
        'samples', 'sample_annotations', 'sample_validations',
        'series', 'series_annotations', 'series_validations',
        'concordant_sample_annotations', 'concordant_sample_tags', 'concordant_sample_validations',
        'concordant_series_annotations', 'concordant_series_tags', 'concordant_series_validations',
        'sample_tags_by_users', 'sample_validations_by_users', 'series_validations_by_users',
    ];

    const bySpeciesHtml = _.join(
        _.map(bySpecies,
              (table) => `<h3>${table}</h3><div id="${table}_by_species"></div><div id="${table}_legenda"></div>`),
        '');

    const elem = document.getElementById(bindto);
    elem.innerHTML = `
    <h3>tags and users</h3>
    <div id="usersAndTags"></div>
    ${bySpeciesHtml}
    `;
    showAll(
        '#usersAndTags',
        _.map(data, ([date, value]) =>
              [date, _.pick(value, ['users', 'tags'])]));

    _.forEach(bySpecies, (table) => {
        showByKeys(
            table,
            _.map(data, ([date, value]) => [date, value[table]]),
            _.includes(['sample_validations_by_users', 'series_validations_by_users'], table) ?
                { mapX: (key) => _.get(users, `${key}`, key) } : { showTotal: true });
    });
}
