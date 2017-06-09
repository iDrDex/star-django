var webpack = require('webpack');
var path = require('path');


module.exports = {
    entry: {
        analysis: './app/analysis',
        stats: './app/stats',
    },
    devtool: 'source-map',
    output: {
        path: path.join(__dirname, 'public'),
        filename: '[name].bundle.js',
        library: ['App', '[name]'],
        libraryTarget: 'window',
    },
    resolve: {
        extensions: ['.js'],
    },
    module: {
        loaders: [
            {
                test: /\.js?$/,
                exclude: /(node_modules|bower_components)/,
                loaders: ['babel-loader?presets[]=es2015'],
            },
            { test: /\.css$/, loader: 'style-loader!css-loader' },
        ],
    },
    devServer: {
        contentBase: './public',
        noInfo: false,
        hot: true,
        inline: true,
    },
};
