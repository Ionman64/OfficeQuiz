var QuestionView = {
    question:undefined,
    oninit:function() {
        this.fetch();
    },
    fetch: function() {
        m.request({
            method: "GET",
            url: "/api/question/:id"
        }).then(function (data) {
            QuestionView.question = data;
        }).catch(function (e) {
            Logger.error("Could not logout from server", e.message);
        });
    },
    view: function() {
        return m(".container-fluid", [
            m(".row", [
                m(".col-md-12", [
                    
                ])
            ])
        ])
    }
}

var ScoreView = {
    oninit:function() {
        this.fetch();
    },
    
}

function setupPage() {
    m.route(document.getElementById("mihtril-table"), "/score", {
        "/score":ScoreView,
        "/question/:id":QuestionView
    });
}

document.addEventListener("DOMContentLoaded", function (event) {
    setupPage();
});