const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// 获取命令行参数 (经验卡片 ID)
const cardId = process.argv[2];

if (!cardId) {
    console.error('❌ 错误：请提供经验卡片 ID');
    console.log('用法：npm run promote <card-id>');
    console.log('示例：npm run promote 005');
    process.exit(1);
}

const runtimeDir = path.join(__dirname, '..', 'docs', 'experience', '01-runtime');
const seedDir = path.join(__dirname, '..', 'docs', 'experience', '00-seed');

// 查找文件
const files = fs.readdirSync(runtimeDir);
const sourceFile = files.find(f => f.includes(cardId));

if (!sourceFile) {
    console.error(`❌ 错误：未找到包含 ID "${cardId}" 的运行时经验卡片`);
    process.exit(1);
}

const sourcePath = path.join(runtimeDir, sourceFile);
const targetPath = path.join(seedDir, sourceFile);

// 读取内容
let content = fs.readFileSync(sourcePath, 'utf-8');

// 提示用户确认 (自动化中的半自动环节)
console.log('\n⚠️  请确认以下内容已去除业务特定逻辑：');
console.log('---');
console.log(content.substring(0, 200) + '...');
console.log('---');
console.log('\n💡 提示：如未泛化，请先用 Cursor AI 重写该内容。');
console.log('按回车继续晋升流程...');

// 等待用户确认 (简单实现)
const readline = require('readline');
const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

rl.question('确认内容已泛化？(y/n): ', (answer) => {
    if (answer.toLowerCase() !== 'y') {
        console.log('❌ 操作已取消');
        rl.close();
        process.exit(0);
    }

    // 复制文件
    fs.copyFileSync(sourcePath, targetPath);
    console.log(`✅ 文件已复制到 ${targetPath}`);

    // 更新 Frontmatter 版本
    console.log('🔧 正在更新版本号...');
    // (此处可添加自动更新 version 字段的逻辑)

    // 创建 Git 分支
    const branchName = `feat/promote-experience-${cardId}`;
    try {
        execSync(`git checkout -b ${branchName}`);
        execSync(`git add ${targetPath}`);
        execSync(`git commit -m "feat: 晋升经验卡片 #${cardId} 到种子库"`);
        console.log(`✅ 已创建分支 ${branchName} 并提交`);
        console.log('\n🚀 下一步：git push upstream ${branchName} 并创建 PR');
    } catch (error) {
        console.error('❌ Git 操作失败，请手动提交');
    }

    rl.close();
});
