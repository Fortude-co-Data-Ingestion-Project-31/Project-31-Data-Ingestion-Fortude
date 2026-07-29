# Project 31: Data Ingestion Engine
# FIT4002-Fortude

This is a data pipeline designed to integrate data from multiple systems, standardise their data formats, then distribute them to appropriate storage systems to allow the collected data to be analysed and queried in a unified way.

This system is composed of:
- **Connectors** to extract data from various platforms including Infor, JIRA, and SharePoint
- **Mappers** to normalise the data into a canonical format and serialise it into the format required
- **Business Rules** to filter, transform, and route data records
- **Storage Systems** to output the processed data to appropriate destinations

## Contributors

| Name                     | Student Email               | Personal Email               |
| ------------------------ | --------------------------- | ---------------------------- |
| Junjie Huang (Joel)      | jhua0145@student.monash.edu | gulityeaten@gmail.com        |
| Naveen Sellathurai       | nsel0009@student.monash.edu | Navboy44@outlook.com         |
| Nag Rohith Chapalamadugu | rcha0087@student.monash.edu | sivasvg1rohith@gmail.com     |
| Rowan Albert Alex        | ralb0005@student.monash.edu | ralbertalex@gmail.com        |
| Sai Ashish Ramishetty    | sram0056@student.monash.edu | sairamishetty58@gmail.com    |
| Sona Hariharan           | shar0108@student.monash.edu | sonahariharan067@gmail.com   |


## Documentation links

- Full Development Guide: https://docs.google.com/document/d/1HHSTL8_dvFfBZY46qxhkSk_gw6rnYG-cDUmNmGnLFsg/edit?usp=sharing
- [Setup](documentation/setup.md)
- [GIT Guidelines](documentation/git-guidelines.md)

## Frontend (src)

- **Install dependencies:**

	```bash
	cd src
	npm install
	```

- **Run development server:**

	```bash
	cd src
	npm run dev
	```