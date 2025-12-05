/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{vue,js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: '#171717', // Neutral 900 (Black-ish)
                secondary: '#525252', // Neutral 600
                success: '#10B981',
                warning: '#F59E0B',
                danger: '#EF4444',
            },
            borderRadius: {
                'xl': '1rem',
                '2xl': '1.5rem',
                '3xl': '2rem',
            }
        },
    },
    plugins: [],
}
