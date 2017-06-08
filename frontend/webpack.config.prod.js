var webpack = require('webpack');
var path = require('path');


module.exports = Object.assign(require('./webpack.config.js'), {
    devtool: 'cheap-source-map',
    output: {
        path: path.join(__dirname, 'dist'),
        filename: 'bundle.js',
    },
    plugins: [
        new webpack.NoErrorsPlugin(),
        new webpack.optimize.UglifyJsPlugin({
            compress: {
                warnings: false,
            },
        }),
    ],
});
