import draw from './plots';
import _ from 'lodash';

window.showForestPlot = function (elem, data) {
    const keys = [
        'studlab', 'TE', 'lower', 'upper', 'n.e',
        'mean.e', 'sd.e', 'n.c', 'mean.c', 'sd.c',
        'w.fixed', 'w.random',
    ];

    const groupedData = data[keys[0]].map((v, i) =>_.zipObject(keys, keys.map(k => data[k][i])));

    var series = _.map(groupedData, (d) => {
        const result = {
            title: d.studlab,
            md: d.TE,
            left: d.lower,
            right: d.upper,
            experimental: {
                total: d['n.e'],
                mean: d['mean.e'],
                sd: d['sd.e'],
            },
            control: {
                total: d['n.c'],
                mean: d['mean.c'],
                sd: d['sd.c'],
            },
            fixedWeight: d['w.fixed'] / data['w.fixed.w'],
            randomWeight: d['w.random'] / data['w.random.w'],
        };
        return result;
    });

    var effects = [
        {
            type: 'Fixed',
            md: data['TE.fixed'],
            left: data['lower.fixed'],
            right: data['upper.fixed'],
            experimentalTotal: _.sum(_.map(series, 'experimental.total')),
            controlTotal: _.sum(_.map(series, 'control.total')),
        },
        {
            type: 'Random',
            md: data['TE.random'],
            left: data['lower.random'],
            right: data['upper.random'],
            experimentalTotal: _.sum(_.map(series, 'experimental.total')),
            controlTotal: _.sum(_.map(series, 'control.total')),

        },
        {
            type: 'Prediction interval',
            md: 0,
            left: data['lower.predict'],
            right: data['upper.predict'],
        },
    ];

    draw(elem, series, effects, data['level.predict']);
};
