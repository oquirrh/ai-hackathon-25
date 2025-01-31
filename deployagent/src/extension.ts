// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from "vscode";
import * as fs from "fs";
import * as path from "path";

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
  // Use the console to output diagnostic information (console.log) and errors (console.error)
  // This line of code will only be executed once when your extension is activated
  console.log('Congratulations, your extension "deployagent" is now active!');

  // The command has been defined in the package.json file
  // Now provide the implementation of the command with registerCommand
  // The commandId parameter must match the command field in package.json
  const disposable = vscode.commands.registerCommand(
    "deployagent.readProjectFiles",
    async () => {
      // The code you place here will be executed every time your command is executed
      // Display a message box to the user

      const workspaceFolders = vscode.workspace.workspaceFolders;
      if (!workspaceFolders || workspaceFolders.length === 0) {
        vscode.window.showErrorMessage(
          "No folder is open. Please open a folder/workspace first."
        );
        return;
      }

      //Use the first workspace folder
      const rootPath = workspaceFolders[0].uri.fsPath;

      //Recursively gather files
      const allFiles = getAllFiles(rootPath);

      //Logs: file paths in an output channel
      const outputChannel = vscode.window.createOutputChannel("Project Files");
      outputChannel.clear();
      outputChannel.appendLine("List of files in the current folder:");
      allFiles.forEach((file) => outputChannel.appendLine(file));
      outputChannel.show(true);

      vscode.window.showInformationMessage(
        `Found ${allFiles.length} files in your folder.`
      );
    }
  );

  context.subscriptions.push(disposable);
}

//Recursively gather all file paths in a directory.
function getAllFiles(dirPath: string, fileList: string[] = []): string[] {
  const entries = fs.readdirSync(dirPath, { withFileTypes: true });
  for (const entry of entries) {
    const entryPath = path.join(dirPath, entry.name);
    if (entry.isDirectory()) {
      getAllFiles(entryPath, fileList);
    } else {
      fileList.push(entryPath);
    }
  }
  return fileList;
}

// This method is called when your extension is deactivated
export function deactivate() {}
