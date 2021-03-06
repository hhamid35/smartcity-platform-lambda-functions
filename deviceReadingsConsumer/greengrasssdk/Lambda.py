#
# Copyright 2010-2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import logging
import re

from io import BytesIO

from greengrass_common.function_arn_fields import FunctionArnFields
from greengrass_ipc_python_sdk.ipc_client import IPCClient, IPCException
from greengrasssdk.utils.testing import mock

# Log messages in the SDK are part of customer's log because they're helpful for debugging
# customer's lambdas. Since we configured the root logger to log to customer's log and set the
# propagate flag of this logger to True. The log messages submitted from this logger will be
# sent to the customer's local Cloudwatch handler.
customer_logger = logging.getLogger(__name__)
customer_logger.propagate = True

valid_base64_regex = '^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{4}|[A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)$'


class InvocationException(Exception):
    pass


class Client:
    def __init__(self, endpoint='localhost', port=None):
        """
        :param endpoint: Endpoint used to connect to IPC.
        :type endpoint: str

        :param port: Deprecated. Will not be used.
        :type port: None
        """
        self.ipc = IPCClient(endpoint=endpoint)

    def invoke(self, **kwargs):
        r"""
        Invokes Lambda function of the given name.

        :Keyword Arguments:
            * *ClientContext* (``bytes``) --
              Optional Base64-encoded data about the invoking client to pass to the Lambda function
            * *FunctionName* (``string``) --
              [REQUIRED]
              The Amazon Resource Name (ARN) of the Lambda function to invoke. Name formats:

              * Qualified ARN - The function ARN with the version suffix. e.g. arn:aws:lambda:aws-region:acct-id:function:helloworld:1
              * Unqualified ARN - The function ARN without the version suffix. e.g. arn:aws:lambda:aws-region:acct-id:function:helloworld
            * *InvocationType* (``string``) --
              Choose from the following options.

              * ``RequestResponse`` (default) - Invoke the Lambda synchronously. Block until the function returns a response or times out.
              * ``Event`` - Invoke the Lambda asynchronously. The response only includes empty payload.
            * *Payload* (``bytes``) --
              Optional input for the Lambda function to invoke.
            * *Qualifier* (``string``) --
              Optional parameter to specify a Lambda function version if it was not included in the FunctionName field.
              If you specify a function version, the API uses the qualified function ARN to invoke a specific Lambda function.
        :returns: (``dict``) --
            * *FunctionError* (``string``) --
              If present, indicates that an error occurred while executing the Lambda function. If an error occurred,
              this field will have one of two values, ``Handled`` or ``Unhandled``. ``Handled`` errors are errors that are reported by the function
              while the ``Unhandled`` errors are those detected and reported by Greengrass Core.
              ``Unhandled`` errors include out of memory errors and function timeouts. Error details are provided in the Payload.
            * *Payload* (``bytes or StreamingBody object``) --
              It is the result returned by the Lambda function. This is present only if the invocation type is ``RequestResponse``.
              In the event of a function error this field contains a message describing the error.
        """

        # FunctionName is a required parameter
        if 'FunctionName' not in kwargs:
            raise ValueError(
                '"FunctionName" argument of Lambda.Client.invoke is a required argument but was not provided.'
            )

        arn_fields = FunctionArnFields(kwargs['FunctionName'])
        arn_qualifier = arn_fields.qualifier

        # A Function qualifier can be provided as part of the ARN in FunctionName, or it can be provided here. The
        # behavior of the cloud is to throw an exception if both are specified but not equal
        extraneous_qualifier = kwargs.get('Qualifier', '')

        if extraneous_qualifier and arn_qualifier and arn_qualifier != extraneous_qualifier:
            raise ValueError('The derived qualifier from the function name does not match the specified qualifier.')

        final_qualifier = arn_qualifier if arn_qualifier else extraneous_qualifier

        try:
            # GGC v1.9.0 or newer
            function_arn = FunctionArnFields.build_function_arn(arn_fields.unqualified_arn, final_qualifier)
        except AttributeError:
            # older GGC version
            raise AttributeError('class FunctionArnFields has no attribute \'build_function_arn\'. build_function_arn '
                                 'is introduced in GGC v1.9.0. Please check your GGC version.')

        # ClientContext must be base64 if given, but is an option parameter
        try:
            client_context = kwargs.get('ClientContext', b'').decode()
        except AttributeError as e:
            customer_logger.exception(e)
            raise ValueError(
                '"ClientContext" argument must be a byte string or support a decode method which returns a string'
            )

        if client_context:
            if not re.match(valid_base64_regex, client_context):
                raise ValueError('"ClientContext" argument of Lambda.Client.invoke must be base64 encoded.')

        # Payload is an optional parameter
        payload = kwargs.get('Payload', b'')
        invocation_type = kwargs.get('InvocationType', 'RequestResponse')
        customer_logger.debug('Invoking local lambda "{}" with payload "{}" and client context "{}"'.format(
            function_arn, payload, client_context))

        # Post the work to IPC and return the result of that work
        return self._invoke_internal(function_arn, payload, client_context, invocation_type)

    @mock
    def _invoke_internal(self, function_arn, payload, client_context, invocation_type="RequestResponse"):
        """
        This private method is seperate from the main, public invoke method so that other code within this SDK can
        give this Lambda client a raw payload/client context to invoke with, rather than having it built for them.
        This lets you include custom ExtensionMap_ values like subject which are needed for our internal pinned Lambdas.
        """
        customer_logger.debug('Invoking Lambda function "{}" with Greengrass Message "{}"'.format(function_arn, payload))

        try:
            invocation_id = self.ipc.post_work(function_arn, payload, client_context, invocation_type)

            if invocation_type == "Event":
                # TODO: Properly return errors based on BOTO response
                # https://boto3.readthedocs.io/en/latest/reference/services/lambda.html#Lambda.Client.invoke
                return {'Payload': b'', 'FunctionError': ''}

            work_result_output = self.ipc.get_work_result(function_arn, invocation_id)
            if not work_result_output.func_err:
                output_payload = StreamingBody(work_result_output.payload)
            else:
                output_payload = work_result_output.payload
            invoke_output = {
                'Payload': output_payload,
                'FunctionError': work_result_output.func_err,
            }
            return invoke_output
        except IPCException as e:
            customer_logger.exception(e)
            raise InvocationException('Failed to invoke function due to ' + str(e))


class StreamingBody(object):
    """Wrapper class for http response payload

    This provides a consistent interface to AWS Lambda Python SDK
    """
    def __init__(self, payload):
        self._raw_stream = BytesIO(payload)
        self._amount_read = 0

    def read(self, amt=None):
        """Read at most amt bytes from the stream.
        If the amt argument is omitted, read all data.
        """
        chunk = self._raw_stream.read(amt)
        self._amount_read += len(chunk)
        return chunk

    def close(self):
        self._raw_stream.close()
