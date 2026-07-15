import os
import shutil
import zipfile
from datetime import datetime

import boto3
from botocore.exceptions import ClientError


class DeploymentManager:

    def __init__(self):

        self.project_name = "assignment3-data-pipeline"
        self.stack_name = "assignment3-data-pipeline"
        self.region = os.environ.get("AWS_REGION", "us-east-1")

        self.alert_email = os.environ.get(
            "ALERT_EMAIL",
            "srushtychintal11204@gmail.com"
        )

        self.project_directory = os.path.dirname(
            os.path.abspath(__file__)
        )

        self.lambda_directory = os.path.join(
            self.project_directory,
            "lambdas"
        )

        self.common_directory = os.path.join(
            self.project_directory,
            "common"
        )

        self.glue_scripts_directory = os.path.join(
            self.project_directory,
            "glue_scripts"
        )

        self.build_directory = os.path.join(
            self.project_directory,
            "build"
        )

        self.template_file = os.path.join(
            self.project_directory,
            "cf_template.yaml"
        )

        self.s3_client = boto3.client(
            "s3",
            region_name=self.region
        )

        self.cloudformation_client = boto3.client(
            "cloudformation",
            region_name=self.region
        )

        self.sts_client = boto3.client(
            "sts",
            region_name=self.region
        )

        self.account_id = self.sts_client.get_caller_identity()[
            "Account"
        ]

        self.code_bucket_name = (
            f"{self.project_name}-code-{self.account_id}-{self.region}"
        )

        self.deployment_id = datetime.utcnow().strftime(
            "%Y%m%d%H%M%S"
        )

        self.lambda_folders = {
            "save_s3_config": "SaveS3ConfigLambdaKey",
            "run_glue_job": "RunGlueJobLambdaKey",
            "glue_success": "GlueSuccessLambdaKey",
            "glue_failure": "GlueFailureLambdaKey"
        }

        self.uploaded_lambda_keys = {}

    def create_build_directory(self):

        if os.path.exists(self.build_directory):
            shutil.rmtree(self.build_directory)

        os.makedirs(self.build_directory)

        print("Build directory created.")

    def create_code_bucket(self):

        try:
            self.s3_client.head_bucket(
                Bucket=self.code_bucket_name
            )

            print(
                f"Code bucket already exists: "
                f"{self.code_bucket_name}"
            )

        except ClientError:

            print(
                f"Creating code bucket: "
                f"{self.code_bucket_name}"
            )

            if self.region == "us-east-1":

                self.s3_client.create_bucket(
                    Bucket=self.code_bucket_name
                )

            else:

                self.s3_client.create_bucket(
                    Bucket=self.code_bucket_name,
                    CreateBucketConfiguration={
                        "LocationConstraint": self.region
                    }
                )

            print("Code bucket created successfully.")

    def add_directory_to_zip(
        self,
        zip_file,
        source_directory,
        zip_directory_name
    ):

        for root, directories, files in os.walk(
            source_directory
        ):

            directories[:] = [
                directory
                for directory in directories
                if directory != "__pycache__"
            ]

            for file_name in files:

                if file_name.endswith(".pyc"):
                    continue

                source_path = os.path.join(
                    root,
                    file_name
                )

                relative_path = os.path.relpath(
                    source_path,
                    source_directory
                )

                zip_path = os.path.join(
                    zip_directory_name,
                    relative_path
                )

                zip_file.write(
                    source_path,
                    zip_path
                )

    def zip_lambda(self, lambda_name):

        lambda_source_directory = os.path.join(
            self.lambda_directory,
            lambda_name
        )

        app_file = os.path.join(
            lambda_source_directory,
            "app.py"
        )

        if not os.path.exists(app_file):

            raise FileNotFoundError(
                f"app.py not found for Lambda: {lambda_name}"
            )

        zip_file_name = f"{lambda_name}.zip"

        zip_file_path = os.path.join(
            self.build_directory,
            zip_file_name
        )

        with zipfile.ZipFile(
            zip_file_path,
            "w",
            zipfile.ZIP_DEFLATED
        ) as zip_file:

            # app.py must be at the ZIP root.
            zip_file.write(
                app_file,
                "app.py"
            )

            # Add the reusable common package.
            self.add_directory_to_zip(
                zip_file,
                self.common_directory,
                "common"
            )

        print(
            f"Created Lambda ZIP: {zip_file_name}"
        )

        return zip_file_path

    def upload_lambda_zip(
        self,
        lambda_name,
        zip_file_path
    ):

        s3_key = (
            f"lambda/{lambda_name}_"
            f"{self.deployment_id}.zip"
        )

        self.s3_client.upload_file(
            zip_file_path,
            self.code_bucket_name,
            s3_key
        )

        self.uploaded_lambda_keys[
            self.lambda_folders[lambda_name]
        ] = s3_key

        print(
            f"Uploaded {lambda_name} to "
            f"s3://{self.code_bucket_name}/{s3_key}"
        )

    def package_and_upload_lambdas(self):

        for lambda_name in self.lambda_folders:

            zip_file_path = self.zip_lambda(
                lambda_name
            )

            self.upload_lambda_zip(
                lambda_name,
                zip_file_path
            )

    def upload_glue_scripts(self):

        glue_script_names = [
            "process_text.py",
            "process_csv.py",
            "process_json.py"
        ]

        for script_name in glue_script_names:

            local_script_path = os.path.join(
                self.glue_scripts_directory,
                script_name
            )

            if not os.path.exists(local_script_path):

                raise FileNotFoundError(
                    f"Glue script not found: {script_name}"
                )

            s3_key = f"glue/{script_name}"

            self.s3_client.upload_file(
                local_script_path,
                self.code_bucket_name,
                s3_key
            )

            print(
                f"Uploaded Glue script to "
                f"s3://{self.code_bucket_name}/{s3_key}"
            )

    def get_template_body(self):

        with open(
            self.template_file,
            "r",
            encoding="utf-8"
        ) as template:

            return template.read()

    def get_stack_parameters(self):

        parameters = [
            {
                "ParameterKey": "ProjectName",
                "ParameterValue": self.project_name
            },
            {
                "ParameterKey": "AlertEmail",
                "ParameterValue": self.alert_email
            },
            {
                "ParameterKey": "CodeBucketName",
                "ParameterValue": self.code_bucket_name
            }
        ]

        for parameter_name, s3_key in (
            self.uploaded_lambda_keys.items()
        ):

            parameters.append({
                "ParameterKey": parameter_name,
                "ParameterValue": s3_key
            })

        return parameters

    def stack_exists(self):

        try:

            self.cloudformation_client.describe_stacks(
                StackName=self.stack_name
            )

            return True

        except ClientError as error:

            error_message = str(error)

            if "does not exist" in error_message:
                return False

            raise

    def deploy_cloudformation(self):

        template_body = self.get_template_body()
        parameters = self.get_stack_parameters()

        if self.stack_exists():

            print(
                f"Updating CloudFormation stack: "
                f"{self.stack_name}"
            )

            try:

                self.cloudformation_client.update_stack(
                    StackName=self.stack_name,
                    TemplateBody=template_body,
                    Parameters=parameters,
                    Capabilities=[
                        "CAPABILITY_NAMED_IAM"
                    ]
                )

                waiter = (
                    self.cloudformation_client.get_waiter(
                        "stack_update_complete"
                    )
                )

                waiter.wait(
                    StackName=self.stack_name
                )

                print(
                    "CloudFormation stack updated successfully."
                )

            except ClientError as error:

                if "No updates are to be performed" in str(error):

                    print(
                        "No CloudFormation changes were found."
                    )

                else:
                    raise

        else:

            print(
                f"Creating CloudFormation stack: "
                f"{self.stack_name}"
            )

            self.cloudformation_client.create_stack(
                StackName=self.stack_name,
                TemplateBody=template_body,
                Parameters=parameters,
                Capabilities=[
                    "CAPABILITY_NAMED_IAM"
                ],
                OnFailure="ROLLBACK"
            )

            waiter = (
                self.cloudformation_client.get_waiter(
                    "stack_create_complete"
                )
            )

            waiter.wait(
                StackName=self.stack_name
            )

            print(
                "CloudFormation stack created successfully."
            )

    def show_stack_outputs(self):

        response = (
            self.cloudformation_client.describe_stacks(
                StackName=self.stack_name
            )
        )

        outputs = response[
            "Stacks"
        ][0].get(
            "Outputs",
            []
        )

        print("\nCloudFormation Outputs")
        print("----------------------")

        for output in outputs:

            print(
                f"{output['OutputKey']}: "
                f"{output['OutputValue']}"
            )

    def deploy(self):

        print("Starting Assignment 3 deployment.\n")

        self.create_build_directory()
        self.create_code_bucket()
        self.package_and_upload_lambdas()
        self.upload_glue_scripts()
        self.deploy_cloudformation()
        self.show_stack_outputs()

        print("\nDeployment completed successfully.")


if __name__ == "__main__":

    deployment_manager = DeploymentManager()

    try:
        deployment_manager.deploy()

    except Exception as error:

        print("\nDeployment failed.")

        print(error)

        raise