var express = require('express');
var session = require('express-session');
var flash = require('connect-flash');
var bodyParser = require('body-parser');
var cookieParser = require('cookie-parser');
var multer = require('multer');
var https = require('https');
var mysql = require('mysql');
var bcrypt = require('bcrypt-nodejs');
var connection = mysql.createConnection(require('./config/dbconnect.json'));
var fs = require('fs');
var app = express();

connection.connect(function(err) {
	if (!err) {
		console.log("Database is connected...\n");
	} else {
		console.log("Error connecting database...\n\n");
	}
});
app.use(express.static("result"));
app.use(cookieParser());
app.use(session({
	secret: 'usc2014fall',
	resave: true,
    saveUninitialized: true
}));
app.set('view engine', 'ejs');
app.use(flash());
app.use(bodyParser.urlencoded({extended: true}));
app.use(multer({dest: 'tmp/'}).single('photo'));
var sessionKey;

app.get('/', function (req, res) {
  sessionKey = req.session;
  if (sessionKey.email) {
  	res.redirect('/main');
  } else {
  	res.render('index.ejs', {message: req.flash('loginMessage')});
  }
});

app.get('/main', function (req, res) {
  sessionKey = req.session;
  if (sessionKey.email) {
    connection.query('SELECT * FROM history', function(err, rows) {
      if (!err) {
        res.render('main.ejs', {record: rows, feedback: req.flash('uploadMessage')});
      } else {
        console.log('Error');
        throw err;
      }
    });
  } else {
  	res.redirect('/');
  }
});

app.get('/signup', function (req, res) {
    res.render('signup.ejs', {message: req.flash('signupMessage')});
});

app.post('/subscribe', function (req, res) {
  var firstname = req.body.firstname;
  var lastname = req.body.lastname;
  var email = req.body.email;
  var password = req.body.password;
  connection.query('SELECT * FROM Users WHERE email LIKE \''+ email + '\'', function(err, rows){
    if (!err) {
      if (rows == "") {
        var user = {
          firstname: firstname,
          lastname: lastname,
          email: email,
          password: bcrypt.hashSync(password, null, null),
          photo: null
        };
        connection.query('INSERT INTO Users SET ?', user, function(err){
          if (err) throw err;
          console.log('User Information > Users');
        });
        var mail = {
          to: email,
          subject: "Smart Home Security Subscription",
          text: "You are successfully subscribed to WigWag Home Security!"
        };
        require('./config/email')(mail);
        sessionKey = req.session;
        sessionKey.email = email;
        res.redirect('/main');
      } else {
         console.log('Already exist...');
         req.flash('signupMessage', 'User already exist. Please try signing up with another email.');
         res.redirect('/signup');
      }
    } else {
    	   console.log('Error');
    	   throw err;
    }
  });
});

app.post('/upload_photo', function (req, res) {
  sessionKey = req.session;
  if (sessionKey.email) {
    connection.query('SELECT * FROM Users WHERE email = ?', [sessionKey.email], function(err, rows) {
      if (err) {
        throw(err);
      } else {
        var id = rows[0].id;
        var originalName = req.file.originalname;
        var format = originalName.substring(originalName.indexOf('.'));
        var file = __dirname + "/photos/subject" + id + format;
        fs.readFile(req.file.path, function(err, data) {
          fs.writeFile(file, data, function(err) {
            if (err) {
                 console.log(err);
            } else {
                 console.log("File uploaded successfully.");
            }
          });
        });
        connection.query('UPDATE Users SET photo = ? WHERE email = ?', [file, sessionKey.email],function(err, rows) {
          if (!err) {
            //var python = require('child_process').spawn('python',["face_recognizer.py"]);
            req.flash('uploadMessage', 'Upload successfully!')
            res.redirect('/main');
          } else {
            console.log('Error');
            throw err;
          }
        });
      }
    });
  } else {
    res.redirect('/');
  }
});

app.post('/signin', function (req, res) {
	var email = req.body.email;
  var password = req.body.password;
  connection.query('SELECT * FROM Users WHERE email = ?', [email], function(err, rows){
  	if (err) throw err;
  	if (rows.length == 0) {
  		req.flash('loginMessage', 'User Not Found');
  		res.redirect('/');
  	} else if (!bcrypt.compareSync(password, rows[0].password)) {
  		req.flash('loginMessage', 'Wrong username or password');
  		res.redirect('/');
  	} else {
  		sessionKey = req.session;
 	   	sessionKey.email = email;
  		res.redirect('/main');
  	}
  });
});

app.get('/logout', function (req, res) {
  req.session.destroy(function(err) {
    if (err) {
      throw(err);
    } else {
      res.redirect('/');
    }
  });
});

var server = https.createServer({
	key: fs.readFileSync('key.pem'),
	cert: fs.readFileSync('cert.pem')
}, app).listen(8081, function () {

  var host = server.address().address
  var port = server.address().port

  console.log("Server listening at http://%s:%s", host, port)

});