var mysql = require('mysql');
var original_pool = mysql.createPool({
    connectionLimit :   1000,
    host     : "twittersentiment.c8olx6nhxh4p.us-east-1.rds.amazonaws.com",
    user     : "cameronpepe",
    password : "password",
    database : "twitterSentiment",
    port     : '3306'
});
var Sentiment = require('sentiment');
var sentiment = new Sentiment();
var labels = require('./labels.json');
var sql = "SELECT date, timestamp, text FROM twitterSentiment.tweetSentiment;";
var valArray = []
original_pool.query(sql, function (err, r) {
    if (err) throw err;
    for (var i =0; i < r.length; i++){
        var row = JSON.parse(JSON.stringify(r[i]));
        var text = row['text'];
        var timestamp = row['timestamp'];
        //console.log(timestamp);
        var date = row['date'];
        text = text.toLowerCase();
        if (text.search('nike') != -1) {

            var result = sentiment.analyze(text);
            var compScore = result.comparative;
            var emotion = 'neutral';
            if (compScore > .3){
                emotion = 'positive';
            }
            if (compScore < -.3){
                emotion = 'negative'
            }
            //console.log(result)

            // Calculate the individual postive or negative influences
            var posScore = 0;
            var negScore = 0;
            var neutralScore = 0;
            for(let i = 0; i < result.positive.length; i++){
                var tokenPos = result.positive[i];
                if(labels[tokenPos]){
                    posScore = posScore + labels[tokenPos]
                }    
            }   
            for(let i = 0; i < result.negative.length; i++){
                var tokenNeg = result.positive[i];
                if(labels[tokenNeg]){
                    negScore = negScore + labels[tokenNeg]
                }    
            }
            var numNeutral = (result.tokens.length - result.words.length);
            //console.log(numNeutral);
            neutralScore = numNeutral/result.tokens.length;
            posScore = posScore/result.tokens.length;
            negScore = negScore/result.tokens.length;
            // We've got relative scores, now just normalize all 3 values so they sum to 1
            var totalSentiment = neutralScore + posScore + negScore;
            if(totalSentiment != 0){
            neutralScore = neutralScore/totalSentiment;
            posScore = posScore/totalSentiment;
            negScore = negScore/totalSentiment;
            }
            else{
                neutralScore = 0;
                posScore = 0;
                negScore = 0;
            }
            
            
            var neutral={"neutralScore":neutralScore};
            var positive={"positiveScore":posScore};
            var negative={"negativeScore":negScore};
            //console.log(neutral, positive, negative);
            date = timestamp.substring(0,10);
            var values = [timestamp, date, 'Nike', text, posScore, negScore, neutralScore]
            valArray.push(values);
            //console.log("This runs");
        }
    }
    console.log("escaped");
    storeTweets(valArray);
})
function storeTweets(vals) {
    // store the text, timestamp, and sentiment in the RDS
    console.log(vals[0][1]);
   /* var sql = "INSERT IGNORE INTO tweetSentimentNew (`timestamp`, `date`, `company`, `text`, `positive`, `negative`, `neutral`) VALUES (?, ?, ?, ?, ?, ?, ?)";
        original_pool.query(sql, values, function (err, response) {
            if (err) throw err;
            console.log(response);
        })*/
    var sql = "INSERT IGNORE INTO tweetSentimentNew (timestamp, date, company, text, positive, negative, neutral) VALUES ?";
    //console.log(vals);
    original_pool.query(sql, [vals], function (err, result) {
        if (err) throw err;
    })
}