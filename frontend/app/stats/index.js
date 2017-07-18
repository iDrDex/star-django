import _ from 'lodash';
import c3 from 'c3';
import 'c3/c3.css';

function showByKeys(bindto, data) {
    const keysData = _.map(data, _.head);
    const keys = _.keys(data[0][1]);

    let dataColumns = {
        total: _.map(data, ([_date, value]) => _.reduce(_.values(value), (a, b) => a + b)),
    };

    _.forEach(keys, (key) => {
        dataColumns[key] = _.map(data, ([_date, value]) => value[key]);
    });

    const chart = c3.generate({
        bindto,
        data: {
            x: 'x',
            columns: _.concat([
                _.concat('x', keysData),
                _.concat('total', dataColumns.total),
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
    });
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

export function showStats(bindto, data) {

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
              (table) => `<h3>${table}</h3><div id="${table}_by_species"></div>`),
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
            `#${table}_by_species`,
            _.map(data, ([date, value]) => [date, value[table]]));
    });
}
