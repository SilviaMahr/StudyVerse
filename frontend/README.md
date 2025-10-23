# Frontend
Following steps must be performed in order to run the angular frontend:

- install node.js ( v20.19.0 or newer) https://angular.dev/reference/versions
- open terminal in your IDE and run following commands:

Navigate from the root (StudyVerse) of the project to "frontend" $\to$ ...\StudyVerse\frontend:
with command:
```
cd frontend
```
Install required packages:
```
npm install
```

Run the build command: 
```
ng build
```

In case the command fails, run:
```
npm install -g @angular/cli
```
Then build the frontend again.

After a successful build, start server: 
```
ng serve
```
Open the application on localhost (you find the link in the terminal).
