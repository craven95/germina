import { Theme as Bootstrap4Theme } from '@rjsf/bootstrap-4';
import Form, { withTheme } from '@rjsf/core';
import validator from '@rjsf/validator-ajv8';
import * as React from 'react';
import * as ReactDOM from 'react-dom/client';

const FormWithTheme = withTheme(Bootstrap4Theme);

const handleSubmit = async ({ formData: fd }) => {
    const body = new FormData();
    Object.entries(fd).forEach(([k, v]) => body.append(k, v));

    const r = await fetch('/submit', { method: 'POST', body });
    const json = await r.json();

    if (r.ok && json.status === 'ok') {
      alert(`✅ Succès : entrée ${json.entry_id} enregistrée.`);
      window.location.reload();
    } else {
      const msg = json.errors
        ? Object.values(json.errors).join('\n')
        : json.error || 'Échec';
      alert(`❌ Erreur :\n${msg}`);
    }
  };


window.renderSurveyForm = async ({schema, ui_schema, form_data, errors, success_message}) => {
  const root = ReactDOM.createRoot(document.getElementById('root'));
  root.render(
    React.createElement(FormWithTheme, {
      schema,
      uiSchema: ui_schema,
      formData: form_data,
      extraErrors: errors,
      onSubmit: handleSubmit,
      validator
    })
  );
  if (success_message) setTimeout(() => alert(success_message), 100);
};

window.JSONSchemaForm = { Form, withTheme, validator };
window.RJSFBootstrap4 = { Theme: Bootstrap4Theme };
