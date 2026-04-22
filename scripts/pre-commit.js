// Windows 兼容的 pre-commit 钩子
const { execSync } = require('child_process');

try {
    console.log('🔍 Running lint-staged...');
    execSync('npx lint-staged', { stdio: 'inherit' });
    console.log('✅ Pre-commit checks passed.');
    process.exit(0);
} catch (error) {
    console.error('❌ Pre-commit checks failed.');
    process.exit(1);
}
