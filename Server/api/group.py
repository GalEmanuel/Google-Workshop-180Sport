from datetime import datetime, date

import flask
from flask import Blueprint, jsonify
from utils import token_required
from models import Group, User, Training

group = Blueprint('group', __name__)


@group.post('/group')
@token_required
def post_group(current_user):
    from main import db
    if current_user.user_type in [3, 4]:
        return jsonify({"success": False,
                        "message": "User cannot create new group, unless it is admin/trainer"}), 401

    try:
        data = flask.request.json
        new_group = Group(day=data['day'], time=data['time'], meeting_place=data['meeting_place'], active_or_not=True)
        db.session.add(new_group)
        db.session.commit()
        return jsonify({"success": True, "group": new_group.to_dict()})
    except:
        return jsonify({"success": False, "message": "Something went wrong"}), 400


@group.delete('/group/<group_id>/')
@token_required
def delete_group(current_user, group_id):
    from main import db
    group_to_delete = db.session.query(Group).filter_by(id=group_id).first()
    if not group_to_delete:
        return jsonify({'success': False, 'message': 'No group found!'})
    if current_user.user_type != 1:
        return jsonify({"success": False,
                        "message": "User cannot delete groups, unless it is admin"}), 401
    # delete matching trainings
    groups_trainings = group_to_delete.trainings_list
    print(groups_trainings)
    if groups_trainings != "" and groups_trainings is not None:
        trainings_list = groups_trainings.split(",")
        print(trainings_list)
        for training in trainings_list:
            training_from_db = db.session.query(Training).filter_by(id=int(training)).first()
            db.session.delete(training_from_db)
            db.session.commit()
    # Delete group from matching users
    users_from_db = db.session.query(User).all()
    for user in users_from_db:
        if id_in_group(user.group_ids, group_id):
            user.group_ids = remove_group_id_from_user(user.group_ids, group_id)
    db.session.delete(group_to_delete)
    db.session.commit()
    return jsonify({"success": True,
                    "message": "Group: " + group_id + " was deleted successfully"}), 200


@group.get('/group/<group_id>/')
@token_required
def get_group(current_user, group_id):
    from main import db
    group_from_db = db.session.query(Group).filter_by(id=group_id).first()
    if not group_from_db:
        return jsonify({'success': False, 'message': 'No group found!'})
    # if current_user.user_type in [3, 4]:
        # return jsonify({"success": False,
                        # "message": "User cannot view group details, unless it is admin/trainer"}), 401
    return jsonify({'success': True, 'Group': group_from_db.to_dict()})


@group.put('/group/<group_id>/')
@token_required
def put_group(current_user, group_id):
    from main import db
    group_from_db = db.session.query(Group).filter_by(id=group_id).first()
    if not group_from_db:
        return jsonify({'success': False, 'message': 'No group found!'})
    if current_user.user_type in [3, 4]:
        return jsonify({"success": False,
                        "message": "User cannot update group details, unless it is admin/trainer"}), 401
    data = flask.request.json
    try:
        for key in data.keys():
            if key == 'day':
                group_from_db.day = data['day']
            if key == 'time':
                group_from_db.time = data['time']
            if key == 'meeting_place':
                group_from_db.meeting_place = data['meeting_place']
            if key == 'active_or_not':
                group_from_db.active_or_not = data['active_or_not']
        db.session.commit()
        return jsonify({"success": True, "user": group_from_db.to_dict()})
    except:
        return jsonify({"success": False, "message": "Something went wrong"}), 400


def listToString(lst):
    # initialize an empty string
    str1 = ""

    # traverse in the string
    for ele in lst:
        str1 += (ele + ",")

        # return string
    return str1[:-1]


@group.put('/delete_user_from_group/<group_id>/')
@token_required
def delete_user_from_group(current_user, group_id):
    from main import db
    group_from_db = db.session.query(Group).filter_by(id=group_id).first()
    if not group_from_db:
        return jsonify({'success': False, 'message': 'No group found!'})
    if current_user.user_type in [3, 4]:
        return jsonify({"success": False,
                        "message": "User cannot add users to group details, unless it is admin/trainer"}), 401
    try:
        data = flask.request.json
        user_id = int(data['user_id'])
        user_from_db = db.session.query(User).filter_by(id=user_id).first()
        if not user_from_db:
            return jsonify({'success': False, 'message': 'No user found!'})
        groups_string = user_from_db.group_ids
        if groups_string == "":
            return jsonify({'success': False, 'message': 'User is not part of any group'}), 400
        else:
            groups_list = groups_string.split(",")
        if str(group_id) not in groups_list:
            return jsonify({'success': False, 'message': 'User is not part of this group!'}), 400
        groups_list.remove(str(group_id))
        user_from_db.group_ids = listToString(groups_list)
        db.session.commit()
        return jsonify({"success": True, "message": "Group was updated successfully"}), 200
    except:
        return jsonify({"success": False, "message": "Something went wrong"}), 400


@group.put('/add_user_to_group/<group_id>/')
@token_required
def add_user_to_group(current_user, group_id):
    from main import db
    group_from_db = db.session.query(Group).filter_by(id=group_id).first()
    if not group_from_db:
        return jsonify({'success': False, 'message': 'No group found!'})
    if current_user.user_type in [3, 4]:
        return jsonify({"success": False,
                        "message": "User cannot add users to group details, unless it is admin/trainer"}), 401
    try:
        data = flask.request.json
        user_id = int(data['user_id'])
        user_from_db = db.session.query(User).filter_by(id=user_id).first()
        if not user_from_db:
            return jsonify({'success': False, 'message': 'No user found!'})
        groups_string = user_from_db.group_ids
        if groups_string == "" or groups_string is None:
            groups_list = []
        else:
            groups_list = groups_string.split(",")
        if str(group_id) in groups_list:
            return jsonify({'success': False, 'message': 'User is already part of the group!'}), 400
        groups_list.append(str(group_id))
        user_from_db.group_ids = listToString(groups_list)
        db.session.commit()
        return jsonify({"success": True, "message": "Group was updated successfully"}), 200
    except:
        return jsonify({"success": False, "message": "Something went wrong"}), 400


def id_in_group(group_ids, group_id):
    if group_ids == "" or group_ids is None:
        return False
    else:
        groups_list = group_ids.split(",")
    if group_id in groups_list:
        return True
    return False


def remove_group_id_from_user(user_groups, group_id):
    groups_list = user_groups.split(",")
    groups_list.remove(group_id)
    return listToString(groups_list)


@group.get('/get_all_users_by_group/<group_id>/')
@token_required
def get_all_users_by_group(current_user, group_id):
    from main import db
    group_from_db = db.session.query(Group).filter_by(id=group_id).first()
    if not group_from_db:
        return jsonify({'success': False, 'message': 'No group found!'})
    if current_user.user_type in [3, 4]:
        return jsonify({"success": False,
                        "message": "User cannot add users to group details, unless it is admin/trainer"}), 401
    try:
        users_from_db = db.session.query(User).all()
        list_of_users = []
        for user in users_from_db:
            if user.user_type in [3, 4] and id_in_group(user.group_ids, group_id):
                list_of_users.append(user.to_dict())
        return jsonify({"success": True,
                        "users": list_of_users}), 200
    except:
        return jsonify({"success": False, "message": "Something went wrong"}), 400


@group.get('/get_all_trainers_by_group/<group_id>/')
@token_required
def get_all_trainers_by_group(current_user, group_id):
    from main import db
    group_from_db = db.session.query(Group).filter_by(id=group_id).first()
    if not group_from_db:
        return jsonify({'success': False, 'message': 'No group found!'})
    if current_user.user_type in [3, 4]:
        return jsonify({"success": False,
                        "message": "User cannot add users to group details, unless it is admin/trainer"}), 200
    try:
        users_from_db = db.session.query(User).all()
        list_of_users = []
        for user in users_from_db:
            if user.user_type in [2] and id_in_group(user.group_ids, group_id):
                list_of_users.append(user.to_dict())
        return jsonify({"success": True,
                        "trainers": list_of_users}), 200
    except:
        return jsonify({"success": False, "message": "Something went wrong"}), 400


@group.get('/get_all_trainings_by_group/<group_id>/')
@token_required
def get_all_trainings_by_group(current_user, group_id):
    from main import db
    group_from_db = db.session.query(Group).filter_by(id=group_id).first()
    if not group_from_db:
        return jsonify({'success': False, 'message': 'No group found!'})
    if current_user.user_type in [3, 4]:
        return jsonify({"success": False,
                        "message": "User cannot add users to group details, unless it is admin/trainer"}), 401
    try:
        trainings_from_db = db.session.query(Training).all()
        list_of_trainings = []
        for training in trainings_from_db:
            if training.group_id == group_id:
                list_of_trainings.append(training.to_dict())
        return jsonify({"success": True,
                        "trainings": list_of_trainings}), 200
    except:
        return jsonify({"success": False, "message": "Something went wrong"}), 400


@group.get('/get_all_dates_by_group/<group_id>/')
@token_required
def get_all_dates_by_group(current_user, group_id):
    from main import db
    group_from_db = db.session.query(Group).filter_by(id=group_id).first()
    if not group_from_db:
        return jsonify({'success': False, 'message': 'No group found!'})
    if current_user.user_type in [3, 4]:
        return jsonify({"success": False,
                        "message": "User cannot view group details, unless it is admin/trainer"}), 401
    try:
        trainings_from_db = db.session.query(Training).all()
        list_of_dates = []
        for training in trainings_from_db:
            if training.group_id == int(group_id):
                if training.date < datetime.today().date():
                    list_of_dates.append(training.date)
        return jsonify({"success": True,
                        "dates": list_of_dates}), 200
    except:
        return jsonify({"success": False, "message": "Something went wrong"}), 400
