module.exports = {
    "env": {
        "browser": true,
        "es2021": true,
        "node": true
    },
    "extends": "eslint:recommended",
    "parserOptions": {
        "ecmaVersion": "latest",
        "sourceType": "module"
    },
    "rules": {
        "no-unused-vars": "warn",
        "no-undef": "error",
        "semi": ["error", "always"],
        "quotes": ["warn", "single"],
        "indent": ["warn", 4],
        "no-console": "off",
        "no-throw-literal": "error",
        "eqeqeq": ["error", "always"],
        "curly": ["error", "all"],
        "no-var": "error",
        "prefer-const": "warn"
    }
};
