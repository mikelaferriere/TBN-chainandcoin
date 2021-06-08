import pac from './package.json';
import path from "path";
import webpack, { Configuration } from "webpack";
import HtmlWebpackPlugin from "html-webpack-plugin";
import ForkTsCheckerWebpackPlugin from "fork-ts-checker-webpack-plugin";
import { TsconfigPathsPlugin } from "tsconfig-paths-webpack-plugin";

const webpackConfig = (env: { production: boolean; development: boolean; }): Configuration => ({
  entry: "./src/index.tsx",
  ...(env.production || !env.development ? {} : { devtool: "eval-source-map" }),
  resolve: {
    extensions: [".ts", ".tsx", ".js"],
    plugins: [new TsconfigPathsPlugin()]
  },
  output: {
    path: path.join(__dirname, "/dist"),
    filename: "build.js"
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        loader: "ts-loader",
        options: {
          transpileOnly: true
        },
        exclude: /dist/
      },
      {
        test: /\.css$/i,
        use: ['style-loader', 'css-loader'],
      },
    ]
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: "./public/index.html",
      favicon: "./public/favicon.ico",
      filename: "./index.html",
      manifest: "./public/manifest.json"
    }),
    new webpack.DefinePlugin({
      "process.env.PRODUCTION": env.production || !env.development,
      "process.env.NAME": JSON.stringify(pac.name),
      "process.env.VERSION": JSON.stringify(pac.version)
    }),
    new ForkTsCheckerWebpackPlugin({
      eslint: {
        files: "./src/**/*.{ts,tsx,js,jsx}" // required - same as command `eslint ./src/**/*.{ts,tsx,js,jsx} --ext .ts,.tsx,.js,.jsx`
      }
    })
  ]
});

export default webpackConfig;
