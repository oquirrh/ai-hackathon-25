import * as vscode from "vscode";
import { exec } from "child_process";
import * as path from "path";
import * as os from "os";
import simpleGit from "simple-git";

export function activate(context: vscode.ExtensionContext) {
  let disposable = vscode.commands.registerCommand(
    "deployagent.runDeployAgent",
    async () => {
      const workspaceFolders = vscode.workspace.workspaceFolders;
      if (!workspaceFolders) {
        vscode.window.showErrorMessage(
          "No workspace is open. Please open a folder."
        );
        return;
      }

      const workspacePath = workspaceFolders[0].uri.fsPath;
      const repoUrl = "https://github.com/oquirrh/ai-hackathon-25.git";
      const projectName = "ai-hackathon-25";
      const projectPath = path.join(workspacePath, projectName);
      const branchName = "master"; // The branch you want to checkout

      // Directly define environment variables
      const envVars = {
        ...process.env, // Preserve existing environment variables
        OPENROUTER_API_KEY: "",
        PINECONE_API_KEY: "",
        PINECONE_INDEX: "terraform-docs",
      };

      vscode.window.showInformationMessage(
        `Cloning ${repoUrl} into ${projectPath}...`
      );

      try {
        await cloneRepo(repoUrl, projectPath, branchName);
        await setupPythonEnvironment(projectPath);
        await runDeployScript(projectPath, workspacePath, envVars);
        vscode.window.showInformationMessage(
          "Python project deployed successfully!"
        );
      } catch (error: any) {
        vscode.window.showErrorMessage(`Deployment failed: ${error.message}`);
      }
    }
  );

  context.subscriptions.push(disposable);
}

async function cloneRepo(
  repoUrl: string,
  projectPath: string,
  branchName: string
) {
  const git = simpleGit();

  // Remove existing directory (cross-platform way)
  try {
    await vscode.workspace.fs.delete(vscode.Uri.file(projectPath), {
      recursive: true,
    });
  } catch {
    // Ignore errors if the directory does not exist
  }

  // Clone the repo
  await git.clone(repoUrl, projectPath);
  vscode.window.showInformationMessage(`Repository cloned successfully!`);

  // Checkout the specific branch
  const gitProject = simpleGit(projectPath);
  await gitProject.checkout(branchName); //TODO: Have to remove it
  vscode.window.showInformationMessage(`Checked out branch: ${branchName}`);
}

async function setupPythonEnvironment(projectPath: string) {
  return new Promise((resolve, reject) => {
    const venvCommand =
      os.platform() === "win32"
        ? "python -m venv venv"
        : "python3 -m venv venv";
    exec(venvCommand, { cwd: projectPath }, (error) => {
      if (error) {
        return reject(
          new Error(`Failed to create virtual environment: ${error.message}`)
        );
      }

      const activateCmd =
        os.platform() === "win32"
          ? ".\\venv\\Scripts\\activate && "
          : "source venv/bin/activate && ";
      exec(
        `${activateCmd}pip install -r requirements.txt`,
        { cwd: projectPath },
        (error) => {
          if (error) {
            return reject(
              new Error(`Failed to install dependencies: ${error.message}`)
            );
          }
          vscode.window.showInformationMessage(
            "Python environment setup complete."
          );
          resolve(true);
        }
      );
    });
  });
}

async function runDeployScript(
  projectPath: string,
  workspacePath: string,
  envVars: NodeJS.ProcessEnv
) {
  return new Promise((resolve, reject) => {
    const venvPython =
      os.platform() === "win32"
        ? path.join(projectPath, "venv", "Scripts", "python.exe")
        : path.join(projectPath, "venv", "bin", "python3");

    // Ensure the deploy script runs using the virtual environment Python
    exec(
      `${venvPython} terraform-template-expert/pipeline.py "${workspacePath}"`,
      { cwd: projectPath, env: envVars },
      (error, stdout, stderr) => {
        if (error) {
          return reject(
            new Error(`Deploy script failed: ${stderr || error.message}`)
          );
        }
        vscode.window.showInformationMessage(
          "Deploy script executed successfully."
        );
        resolve(true);
      }
    );
  });
}

export function deactivate() {}
