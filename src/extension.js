import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { LanguageClient } from 'vscode-languageclient/node';

let client;

export function activate(context) {
    console.log('¡Iniciando activación de la extensión Heza!');

    const hezaExecutable = 'C:/heza/heza.exe';

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
        const fileName = path.basename(filePath);

        const terminalName = 'Heza';
        let terminal = vscode.window.terminals.find(t => t.name === terminalName);
        if (!terminal) {
            terminal = vscode.window.createTerminal(terminalName);
        }
        terminal.show();

        const command = `"${hezaExecutable}" "${filePath}"`;
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