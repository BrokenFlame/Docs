# System Interface Table
A system interface table contains metadata about communication between two systems. 
It is not there to provide technical specifications or implementation details, please refer to protocol and messaging flow documents for this. 
It provides a high level information for analyst, governance and security teams to understand a systems interfaces.

Below is a System Inferace table template

| System Interface |
| ------------------------------------------------------------------------------------------------------- |
| ID            | Document ID                                                                             |
| ------------- | --------------------------------------------------------------------------------------- | 
| Source System | The system the information flows from                                                   |
| ------------- | --------------------------------------------------------------------------------------- |
| Target System | The system that informatin flows to                                                     |
| ------------- | --------------------------------------------------------------------------------------- |
| Description   | A description of the purpose of the interface                                           |
| ------------- | ----------------------------------------------------------------------------------------|
| Frequency     | How often the information needs to be passed ( Real-time), once per day, monthly, etc ) |
| ------------- | ----------------------------------------------------------------------------------------|

| Interface Objects                                                                                                                                                                                      |
| :-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------:|

| Object           | Field                | Data Dictionary ID                                            | Validation Rules |
| ---------------- | -------------------- | ------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Business Object  | Field within Object  | Reference to Data Dictionary that defines the business object | Specific rules on validating data, leave blank if the Data Dictionary buisness rules suffice |
