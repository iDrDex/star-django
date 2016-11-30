import * as d3 from 'd3';
import _ from 'lodash';
import { scaleLinear } from 'd3-scale';
import format from './format';
import './style/style.css';

function leftTable(spaceLen, titleLen, valueLen) {
    let title = [
        {
            title: 'Study',
            getter: d => d.title,
            x: 0,
            effectsPlot: d => d.type,
            'text-anchor': 'start',
            'font-weight': 'bold',
        },
    ];
    let values = _.map([
        {
            title: 'Total',
            getter: d => d.experimental.total,
            effectsPlot: d => d.experimentalTotal,
        },
        {
            title: 'Mean',
            getter: d => format.f2(d.experimental.mean),
        },
        {
            title: 'SD',
            getter: d => format.f2(d.experimental.sd),
        },
        {
            title: 'Total',
            getter: d => d.control.total,
            effectsPlot: d => d.controlTotal,
        },
        {
            title: 'Mean',
            getter: d => format.f2(d.control.mean),
        },
        {
            title: 'SD',
            getter: d => format.f2(d.control.sd),
        },
    ], (item, index) => _.merge(item, { x: titleLen + spaceLen * index + valueLen * index }));
    return [...title, ...values];
};

function rightTable() {
    return [
        {
            title: 'MD',
            getter: d => format.f2(d.md),
            x: 0,
            effectsPlot: d => format.f2(d.md),
        },
        {
            title: format.p0(data['level.predict']) + '-CI',
            getter: d =>'[' + format.f2(d.left) + ',' + format.f2(d.right) + ']',
            x: 80,
            effectsPlot: d => '[' + format.f2(d.left) + ',' + format.f2(d.right) + ']',
        },
        {
            title: 'w(fixed)',
            getter: d => format.p1(d.fixedWeight),
            x: 140,
        },
        {
            title: 'w(random)',
            getter: d => format.p1(d.randomWeight),
            x: 200,
        },
    ];
};

function legendLeft(selection) {
    _.map(leftTable(10, 100, 50), item => {
        selection.append('text')
            .attr('text-anchor', _.get(item, 'text-anchor', 'end'))
            .attr('x', item.x)
            .attr('y', 30)
            .text(item.title);
    });

    selection.append('text')
        .attr('text-anchor', 'end')
        .attr('x', 220)
        .attr('y', 10)
        .text('Experemental');

    selection.append('text')
        .attr('text-anchor', 'end')
        .attr('x', 400)
        .attr('y', 10)
        .text('Control');
}

function legendRight(selection) {
    _.map(rightTable(), item => {
        selection.append('text')
            .attr('text-anchor', 'end')
            .attr('x', item.x)
            .attr('y', 10)
            .text(item.title);
    });
};

function getPoints(series, xScale, yScale) {
    return (d, i) => {
        const index = i + series.length + 0.87;

        const x1 = xScale(d.left);
        const y1 = yScale(index);

        const x2 = xScale(d.md);
        const y2 = yScale(index + 0.2);

        const x3 = xScale(d.right);
        const y3 = yScale(index);

        const x4 = xScale(d.md);
        const y4 = yScale(index - 0.2);

        return `${x1},${y1} ${x2},${y2} ${x3},${y3} ${x4},${y4}`;
    };
};

function getPointsInit(series, xScale, yScale) {
    return (d, i) => {
        const index = i + series.length + 0.87;

        const x1 = xScale(d.md);
        const y1 = yScale(index);

        const x2 = xScale(d.md);
        const y2 = yScale(index);

        const x3 = xScale(d.md);
        const y3 = yScale(index);

        const x4 = xScale(d.md);
        const y4 = yScale(index);

        return `${x1},${y1} ${x2},${y2} ${x3},${y3} ${x4},${y4}`;
    };
};

export default function(series, effects) {
    const positions = series.length + effects.length + 1;

    const right = 250;
    const left = 300;
    const width = 300;
    const room = 30;
    const margin = { right, left, top: 40, bottom: 20, };
    const outerWidth = margin.left + width + margin.right;
    const outerHeight = room * positions;
    const height = outerHeight - margin.top - margin.bottom;

    const xMin = _.min(_.flatten([_.map(series, 'left'), _.map(effects, 'left')]));
    const xMax = _.max(_.flatten([_.map(series, 'right'), _.map(effects, 'right')]));

    const xScale = scaleLinear()
        .domain([xMin, xMax])
        .range([0, width]);

    const yScale = scaleLinear()
        .domain([0, positions])
        .range([0, height]);

    const maxTotal = _.max(_.map(series, d => d.experimental.total + d.control.total));
    const totalScale = scaleLinear()
        .domain([0, maxTotal])
        .range([2, 10]);

    const xAxis = d3.svg.axis()
        .scale(xScale)
        .ticks(6)
        .orient('bottom');

    const yAxis = d3.svg.axis()
        .scale(yScale)
        .ticks('')
        .orient('left');

    const svg = d3.select('body').append('svg')
        .attr('width', outerWidth)
        .attr('height', outerHeight)
        .style({ 'font-size': '13px' });

    svg.append('g')
        .attr('transform', 'translate(' + margin.left + ',' + (height + margin.top) + ')')
        .call(xAxis);

    svg.append('g')
        .attr('transform', 'translate(' + (margin.left + xScale(0)) + ',' +  margin.top + ')')
        .call(yAxis);

    svg.append('g')
        .attr('class', 'legend')
        .call(legendLeft);

    svg.append('g')
        .attr('transform', 'translate(' + (margin.left + width) + ',0)')
        .attr('class', 'legend')
        .call(legendRight);

    const plots = svg.selectAll('g.plot')
                    .data(series)
                    .enter()
                    .append('g')
                    .attr('class', 'plot');

    const line = plots.append('g')
            .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

    line.append('line')
        .attr('class', 'plot')
        .attr('x1', d => xScale(d.md))
        .attr('y1', (d, i) => yScale(i + 0.37))
        .attr('x2', d=>xScale(d.md))
        .attr('y2', (d, i) => yScale(i + 0.37))
        .style({ stroke: 'rgb(1,164,164)', 'stroke-width': 2 })
        .transition().duration(2000)
        .attr('x1', d => xScale(d.left))
        .attr('x2', d=>xScale(d.right));

    line.append('circle')
        .attr('cx', d => xScale(d.md))
        .attr('cy', (d, i) => yScale(i + 0.37))
        .attr('r', 0)
        .style({ fill: 'rgb(17,63,164)', stroke: 'rgb(17.63.164)', 'stroke-width': 1 })
        .transition().duration(2000)
        .attr('r', d => totalScale(d.experimental.total + d.control.total));

    const texts = plots.append('g')
        .attr('transform', 'translate(0,' + margin.top + ')');

    _.map(leftTable(10, 100, 50), item => {
        texts.append('text')
            .attr('text-anchor', _.get(item, 'text-anchor', 'end'))
            .attr('x', item.x)
            .attr('y', (d, i)=> yScale(i + 0.5))
            .text(item.getter);
    });

    const effect_plots = svg.selectAll('g.effect_plots')
        .data(effects)
        .enter()
        .append('g')
        .attr('class', 'effect_plots');

    effect_plots.append('g')
        .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')')
        .append('polygon')
            .attr('points', getPointsInit(series, xScale, yScale))
            .style({ fill: 'rgb(241,141,5)', stroke: 'rgb(241,141,5)', 'stroke-width': 1 })
            .transition().duration(2000)
            .attr('points', getPoints(series, xScale, yScale));

    const effect_texts = effect_plots.append('g')
        .attr('transform', 'translate(0,' + (margin.top + yScale(series.length + 1)) + ')');

    _.map(leftTable(10, 100, 50), item => {
        if (!!item.effectsPlot) {
            effect_texts.append('text')
                .attr('text-anchor', _.get(item, 'text-anchor', 'end'))
                .attr('x', item.x)
                .attr('y', (d, i)=> yScale(i))
                .style({ 'font-weight': _.get(item, 'font-weight', 'normal') })
                .text(item.effectsPlot);
        }
    });

    const texts_right = plots.append('g')
        .attr('transform', 'translate(' + (margin.left + width) + ',' + margin.top + ')');

    _.map(rightTable(), item => {
        texts_right.append('text')
            .attr('text-anchor', 'end')
            .attr('x', item.x)
            .attr('y', (d, i)=> yScale(i + 0.5))
            .text(item.getter);
    });

    const effect_texts_right = effect_plots.append('g')
        .attr('transform', 'translate(' + (margin.left + width) + ',' + (margin.top + yScale(series.length + 1)) + ')');

    _.map(rightTable(), item => {
        if (!!item.effectsPlot) {
            effect_texts_right.append('text')
                        .attr('text-anchor', 'end')
                        .attr('x', item.x)
                        .attr('y', (d, i)=> yScale(i))
                .text(item.effectsPlot);
        }
    });
};
