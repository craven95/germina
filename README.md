# Name
Germina

## Description
This project is designed to lower the barrier for individuals—such as graduate students, independent researchers, or anyone needing to conduct a survey—to create questionnaires, manage the underlying database, deploy their application to the Internet, and perform data analysis. By bundling form‐builder interfaces with an intuitive database schema and one–click deployment scripts, users no longer need extensive technical expertise to collect, store, and analyze responses.

Key features include:

    Questionnaire Builder
    A drag‐and‐drop or code‐guided interface allows you to design any kind of survey: multiple choice, free‐text, numeric inputs, date pickers, and more. You can customize question order, group fields into sections, and preview the form on desktop or mobile.

    Database Integration
    Every submission is automatically stored in a structured database (PostgreSQL by default), with built‐in support for schema migrations. Users can review raw data in a user‐friendly admin panel, export CSV or JSON, or connect BI tools directly to the database.

    Flexible Deployment Options
    Whether you want to run everything on your own laptop or spin up a cloud‐hosted instance, this project provides deployment scripts for both Docker–based local hosting and managed cloud platforms (AWS, Azure, Google Cloud). This ensures you retain full control over where your data lives, plus a straightforward way to scale if your survey gains traction.

    End‐to‐End Data Control
    Since users can choose local hosting, private‐cloud installations, or a public cloud provider, you own every byte of your survey data. Encryption (at rest and in transit), role‐based access control, and automated backups are all part of the standard setup. No vendor lock‐in means your data remains portable and under your governance.

    Built‐In Analytics and Reporting
    A lightweight analytics dashboard lets you visualize response distributions, compute summary statistics, and apply simple filters (date ranges, demographics, etc.) directly in the web interface. For more advanced analysis, raw data can be exported or queried through a built‐in API.

By bringing together form creation, database management, deployment tooling, and analytics into a single, user‐friendly package, this project empowers thesis authors and other non‐technical users to run professional‐quality surveys without needing to assemble multiple third‐party services. Users can start locally—testing their survey on a laptop—and later transition to a cloud environment to handle larger respondent pools, all while maintaining full transparency and ownership of their data from end to end.


## Installation
For users : No installation needed. Create an account on the website !

For dev team : you can run interface and api locally just fill :



## Support
cravendiot@gmail.com

## Authors and acknowledgment
Craven

## License
MIT License

Copyright (c) 2025 Germina

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell  
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:  

The above copyright notice and this permission notice shall be included in all  
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR  
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,  
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE  
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER  
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,  
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE  
SOFTWARE.