export default {
    content: ['./index.html', './src/**/*.{ts,tsx}'],
    theme: {
        extend: {
            fontFamily: {
                sans: ['"Space Grotesk"', '"Segoe UI"', 'sans-serif'],
            },
            colors: {
                ink: {
                    950: '#040816',
                    900: '#07111f',
                    800: '#0c1b2d',
                },
                aurora: {
                    500: '#4dd6c2',
                    600: '#1fb79f',
                },
                ember: {
                    400: '#f4b860',
                    500: '#e38c2b',
                },
            },
        },
    },
    plugins: [],
};
