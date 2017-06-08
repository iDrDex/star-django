import _ from 'lodash';
import c3 from 'c3';
import 'c3/c3.css';


export function showStats(bindto, data) {
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
