'use strict';

// This script is used by our Heroku buildpack to build our jsx files
// for production.

const exec = require('child_process').exec;

const config = [
  ['./emotiv/experiment/jsx/new_experiment_step_2.jsx', 'step2'],
  ['./emotiv/dashboard/jsx/dashboard.js', 'dashboard'],
  ['./emotiv/experiment/jsx/experiment_view.js', 'experiment_view'],
  ['./emotiv/static/js/phase_detail.js', 'phase_detail'],
  ['./emotiv/static/js/admin.js', 'admin'],
  ['./emotiv/static/js/components.js', 'components'],
  ['./emotiv/static/js/sortable.js', 'sortable'],
  ['./emotiv/static/js/criteria_form.js', 'criteria_form']
];

for (let module of config) {
  exec(
    `npm run babel -- -o emotiv/static/js/${module[1]}.bundle.js ${module[0]} `,
    err => {
      if (err) {
        console.log(err);
      }
    }
  );
}
