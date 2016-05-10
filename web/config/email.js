var nodemailer = require('nodemailer');

var transporter = nodemailer.createTransport('smtps://**@smtp.gmail.com');

module.exports = function(mail) {
	var mailOptions = {
        from: '"yourname" <youremail>', 
        to: mail.to, 
        subject: mail.subject,
        text: mail.text,
        html: '<b>Please do not reply to this email address.</b>' 
    };
 
    transporter.sendMail(mailOptions, function(error, info){
        if(error){
            return console.log(error);
        }
        console.log('Message sent: ' + info.response);
    });
};