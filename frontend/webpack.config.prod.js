var webpack = require('webpack');
var path = require('path');


module.exports = Object.assign(require('./webpack.config.js'), {
    devtool: 'cheap-source-map',
    plugins: [
        new webpack.NoErrorsPlugin(),
        new webpack.optimize.UglifyJsPlugin({
            compress: {
                warnings: false,
            },
        }),
    ],
});
