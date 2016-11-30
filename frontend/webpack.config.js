var webpack = require('webpack');
var path = require('path');

module.exports = {
    entry: [
    './app/index',
    ],
    devtool: 'source-map',
    output: {
        path: path.join(__dirname, 'public'),
        filename: 'bundle.js',
    },
    resolve: {
        extensions: ['', '.js'],
    },
    module: {
        loaders: [
          {
            test: /\.js?$/,
            exclude: /(node_modules|bower_components)/,
            loaders: ['babel?presets[]=es2015'],
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
    plugins: [
    new webpack.NoErrorsPlugin(),
    ],
};
