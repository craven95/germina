'use client';

import validator from '@rjsf/validator-ajv8';
import { withTheme } from '@rjsf/core';
import { Theme as Bootstrap4Theme } from '@rjsf/bootstrap-4';

const FormWithTheme = withTheme(Bootstrap4Theme);

export default function JsonFormRenderer({
  schema,
  uiSchema,
}: {
  schema: any;
  uiSchema?: any;
}) {
  return (
    <div>
        <FormWithTheme
        schema={schema}
        uiSchema={uiSchema}
        validator={validator}
        className="form-container"
      />
    </div>
  );
}
