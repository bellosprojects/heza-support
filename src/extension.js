import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import * as child_process from 'child_process';
import * as https from 'https';
import * as url from 'url';
import { LanguageClient } from 'vscode-languageclient/node';

let client;

const REPO_OWNER = "bellosprojects";
const REPO_NAME = "Heza-Lang";
const MAX_REDIRECTS = 5;

// Función para seguir redirecciones y obtener la URL final de descarga
function followRedirects(downloadUrl, redirectCount = 0) {
    return new Promise((resolve, reject) => {
        if (redirectCount > MAX_REDIRECTS) {
            return reject(new Error('Demasiadas redirecciones.'));
        }

        const options = {
            method: 'GET',
            headers: { 'User-Agent': 'VSCode-Heza-Extension' }
        };

        https.get(downloadUrl, options, (response) => {
            const status = response.statusCode || 0;
            if (status >= 300 && status < 400 && response.headers.location) {
                // Seguir redirección
                const location = response.headers.location;
                const nextUrl = location.startsWith('http') ? location : url.resolve(downloadUrl, location);
                console.log(`Redirigiendo a: ${nextUrl}`);
                followRedirects(nextUrl, redirectCount + 1).then(resolve, reject);
            } else if (status === 200) {
                resolve(downloadUrl); // URL final
            } else {
                reject(new Error(`Código de estado HTTP ${status} al intentar descargar.`));
            }
        }).on('error', reject);
    });
}

function checkHezaInstalled() {
    return new Promise((resolve) => {
        const command = process.platform === 'win32' ? 'where heza' : 'which heza';

        child_process.exec(command, (error) => {
            resolve(!error);
        });
    });
}

async function getHezaSetupDownloadUrl() {
    return new Promise((resolve, reject) => {
        const options = {
            hostname: 'api.github.com',
            path: `/repos/${REPO_OWNER}/${REPO_NAME}/releases/latest`,
            headers: {
                'User-Agent': 'VSCode-Heza-Extension'
            }
        };

        const req = https.get(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    const json = JSON.parse(data);
                    const assets = json.assets || [];

                    const asset = assets.find(a => 
                        a.name && a.name.toLowerCase().includes('windows') && a.name.endsWith('.exe')
                    );

                    if(asset && asset.browser_download_url){
                        console.log(`URL encontrada: ${asset.browser_download_url}`);
                        resolve(asset.browser_download_url);
                    } else {
                        reject(new Error('No se encontro un ejecutable para Windows en la ultima release.'));
                    }
                } catch (e) {
                    reject(new Error('Error al parsear la respuesta de GitHub: ' + e.message));
                }
            });
        });

        req.on('error', (e) => {
            reject(new Error('Error al conectar con GitHub: ' + e.message));
        });

        req.end();
    });
}

async function downloadHezaSetup(context) {
    const storagePath = context.globalStoragePath;
    const hezaDir = path.join(storagePath, 'heza');
    const setupPath = path.join(hezaDir, 'HezaSetup-Windows.exe');

    if(!fs.existsSync(hezaDir)) {
        fs.mkdirSync(hezaDir, { recursive: true });
    }

    if(fs.existsSync(setupPath)) {
        return setupPath;
    }

    const downloadUrl = await getHezaSetupDownloadUrl();
    const finalURL = await followRedirects(downloadUrl);

    return new Promise((resolve, reject) => {
        const file = fs.createWriteStream(setupPath);
        https.get(finalURL, (response) => {
            response.pipe(file);
            file.on('finish', () => {
                file.close();
                resolve(setupPath);
            });
            file.on('error', (e) => {
                fs.unlink(setupPath, () => {});
                reject(new Error('Error al escribir el archivo: ' + e.message));
            });
        }).on('error', (e) => {
            fs.unlink(setupPath, () => {});
            reject(new Error('Error al descargar: ' + e.message));
        });
    });
}

function runInstaller(setupPath) {
    return new Promise((resolve, _) => {
        const child = child_process.spawn(setupPath, [], {
            detached: true,
            stdio: 'ignore'
        });
        child.unref();

        resolve();
    });
}

export function activate(context) {
    console.log('¡Iniciando activación de la extensión Heza!');

    let runFileCommand = vscode.commands.registerCommand('heza.runScript', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No hay ningún archivo activo.');
            return;
        }

        const document = editor.document;
        if (document.languageId !== 'heza') {
            vscode.window.showErrorMessage('El archivo activo no es de Heza.');
            return;
        }

        await document.save();

        const filePath = document.uri.fsPath;

        const installed = await checkHezaInstalled();

        if(!installed){
            const answer = await vscode.window.showWarningMessage(
                'El interprete Heza no esta instalado. Es necesario para ejecutar archivos .hz. ¿Quieres descargar el Setup ahora?',
                {
                    modal: true
                },
                'Si'
            );

            if(answer !== 'Si') {
                vscode.window.showErrorMessage('No se puede ejecutar el script sin el interprete Heza.');
                return;
            }

            try {
                let setupPath;
                await vscode.window.withProgress(
                    {
                        location: vscode.ProgressLocation.Notification,
                        title: 'Descargando el instalador de Heza...',
                        cancellable: false
                    },
                    async (progress) => {
                        progress.report({
                            message: 'Obteniendo URL de descarga...'
                        });
                        setupPath = await downloadHezaSetup(context);
                        progress.report({ message: 'Descarga completada'});
                    }
                );

                runInstaller(setupPath);

                await vscode.window.showInformationMessage(
                    'El instalador de Heza se ha iniciado. Por favor, completa la instalacion y luego cierra y vuelve a abrir VS Code para reconocer el Path',
                    { modal: true},
                    "Entendido"
                );

                return;
            } catch (e) {
                vscode.window.showErrorMessage('Error al descargar o instalar Heza: ' + e.message);
                return;
            }
        }

        const terminalName = 'Heza';
        let terminal = vscode.window.terminals.find(t => t.name === terminalName);

        if (!terminal) {
            terminal = vscode.window.createTerminal(terminalName);
        }
        terminal.show();

        const command = `heza "${filePath}"`;
        terminal.sendText(command);
    });

    context.subscriptions.push(runFileCommand);

    const serverModule = context.asAbsolutePath(path.join('server', 'server.py'));

    let pythonExecutable = 'python'; 
    const venvPath = context.asAbsolutePath(path.join('.', '.venv', 'Scripts', 'python.exe'));
    const envPath = context.asAbsolutePath(path.join('.', '.env', 'Scripts', 'python.exe'));

    if (fs.existsSync(venvPath)) {
        pythonExecutable = venvPath;
    } else if (fs.existsSync(envPath)) {
        pythonExecutable = envPath;
    }

    const serverOptions = {
        command: pythonExecutable,
        args: [serverModule]
    };

    const clientOptions = {
        documentSelector: [{ scheme: 'file', language: 'heza' }],
        synchronize: {
            fileEvents: vscode.workspace.createFileSystemWatcher('**/*.heza')
        },
        trace: 'verbose' 
    };

    client = new LanguageClient(
        'hezaLanguageServer',
        'Heza Language Server',
        serverOptions,
        clientOptions
    );

    client.start();
}

export function deactivate() {
    if (!client) return undefined;
    return client.stop();
}