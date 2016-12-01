import * as d3 from 'd3';
import _ from 'lodash';
import { scaleLinear, scalePow } from 'd3-scale';
import format from './format';
import './style/style.css';

const defaultGap = 10;
const fontSize = 12;

const leftTableShape = [
        {
            title: 'Study',
            getter: d => d.title,
            x: 0,
            effectsPlot: d => d.type,
            'text-anchor': 'start',
            'font-weight': 'bold',
            gap: 20,
        },
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
            gap: 20,
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
];

function rightTableShape(levelPredict) {
    return [
        {
            title: 'MD',
            getter: d => format.f2(d.md),
            effectsPlot: d => format.f2(d.md),
        },
        {
            title: format.p0(levelPredict) + '-CI',
            getter: d =>'[' + format.f2(d.left) + ',' + format.f2(d.right) + ']',
            effectsPlot: d => '[' + format.f2(d.left) + ',' + format.f2(d.right) + ']',
            gap: 20,
        },
        {
            title: 'fixed',
            getter: d => format.p1(d.fixedWeight),
        },
        {
            title: 'random',
            getter: d => format.p1(d.randomWeight),
        },
    ];
};

function drawLegendItem(selection) {
    selection.attr('text-anchor', d => _.get(d, 'text-anchor', 'end'))
        .attr('x', d => d.x)
        .attr('y', 30)
        .text(d => d.title);
}

function updateLegend(legendGroup, legendData) {
    if (legendData.length > 6) {
        legendGroup.append('text')
            .attr('text-anchor', 'end')
            .attr('x', legendData[3].x)
            .attr('y', 10)
            .text('Experemental');

        legendGroup.append('text')
            .attr('text-anchor', 'end')
            .attr('x', legendData[6].x)
            .attr('y', 10)
            .text('Control');
    }

    const legend = legendGroup.selectAll('text')
        .data(legendData)
        .call(drawLegendItem);

    legend.enter()
        .append('text')
        .call(drawLegendItem);

    legend.exit().remove();
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

function getTextWidth(text) {
    return getRealTextWidth(text, fontSize,
        "'Ubuntu', 'Helvetica Neue', Helvetica, 'Open Sans', Arial, sans-serif");
};

function getRealTextWidth(text, fontSize, fontFace) {
    var a = document.createElement('canvas');
    var b = a.getContext('2d');
    b.font = fontSize + 'px ' + fontFace;
    return b.measureText(text).width;
};

function getTable(series, tableShape) {
    let x = 0;
    return _.map(tableShape, (shape, index) => {
        const texts = _.map(series, s => shape.getter(s).toString());
        texts.push(shape.title);
        const columnWidth = _.max(_.map(texts, getTextWidth));
        shape.x = x + (shape['text-anchor'] ? 0 : columnWidth);
        x += columnWidth + (shape.gap || defaultGap);
        return shape;
    });
};

export default function(elem, series, effects, levelPredict) {
    const svgWidth = elem.offsetWidth;
    const leftTable = getTable(series, leftTableShape);
    const rightTable = getTable(series, rightTableShape(levelPredict));

    const left = leftTable[leftTable.length - 1].x + defaultGap;
    const right = (rightTable[rightTable.length - 1] || {x:0}).x + defaultGap;

    const positions = series.length + effects.length + 1;

    const width = _.min([430, _.max([svgWidth - left - right - 40, 200])]);
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
    const totalScale = scalePow()
        .exponent(0.5)
        .domain([0, maxTotal])
        .range([2, 10]);

    const xAxis = d3.svg.axis()
        .scale(xScale)
        .ticks(6)
        .orient('bottom');

    const yAxis = d3.svg.axis()
        .scale(yScale)
        .ticks(0)
        .orient('left');

    const svg = d3.select(elem).append('svg')
        .attr('width', outerWidth)
        .attr('height', outerHeight)
        .style({ 'font-size': fontSize + 'px' });

    svg.append('g')
        .attr('transform', 'translate(' + margin.left + ',' + (height + margin.top) + ')')
        .call(xAxis);

    svg.append('g')
        .attr('transform', 'translate(' + (margin.left + xScale(0)) + ',' +  margin.top + ')')
        .call(yAxis);

    const leftLegendGroup = svg.append('g')
        .attr('class', 'legend');
    updateLegend(leftLegendGroup, leftTable);

    const rightLegendGroup = svg.append('g')
        .attr('transform', 'translate(' + (margin.left + width + defaultGap) + ',0)')
        .attr('class', 'legend');
    updateLegend(rightLegendGroup, rightTable);

    //setTimeout(() => {
        //console.log('update');
        //updateLegend(leftTable);
    //}, 3000);

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
        .transition().duration(500)
        .attr('x1', d => xScale(d.left))
        .attr('x2', d=>xScale(d.right));

    line.append('circle')
        .attr('cx', d => xScale(d.md))
        .attr('cy', (d, i) => yScale(i + 0.37))
        .attr('r', 0)
        .style({ fill: 'rgb(17,63,164)', stroke: 'rgb(17.63.164)', 'stroke-width': 1 })
        .transition().duration(500)
        .attr('r', d => totalScale(d.experimental.total + d.control.total));

    const texts = plots.append('g')
        .attr('transform', 'translate(0,' + margin.top + ')');

    _.map(leftTable, item => {
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
            .transition().duration(500)
            .attr('points', getPoints(series, xScale, yScale));

    const effect_texts = effect_plots.append('g')
        .attr('transform', 'translate(0,' + (margin.top + yScale(series.length + 1)) + ')');

    _.map(leftTable, item => {
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
        .attr('transform', 'translate(' + (margin.left + width + defaultGap) + ',' + margin.top + ')');

    _.map(rightTable, item => {
        texts_right.append('text')
            .attr('text-anchor', 'end')
            .attr('x', item.x)
            .attr('y', (d, i)=> yScale(i + 0.5))
            .text(item.getter);
    });

    const effect_texts_right = effect_plots.append('g')
        .attr('transform', 'translate(' + (margin.left + width + defaultGap) + ',' + (margin.top + yScale(series.length + 1)) + ')');

    _.map(rightTable, item => {
        if (!!item.effectsPlot) {
            effect_texts_right.append('text')
                        .attr('text-anchor', 'end')
                        .attr('x', item.x)
                        .attr('y', (d, i)=> yScale(i))
                .text(item.effectsPlot);
        }
    });
};
